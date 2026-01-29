from __future__ import annotations

from dataclasses import dataclass, field
import logging
import threading
import time
from collections.abc import Callable
from inspect import Parameter, Signature, signature
from typing import Any

import pika

from .config import RabbitMQConfig
from .protocol import build_error_response, build_ok_response, build_progress
from .rabbitmq import connect_blocking, declare_rpc_topology, declare_worker_queue
from .utils.object_encoder_decoder import decode_json, encode_json

logger = logging.getLogger("tanu.worker")

Handler = Callable[..., Any]
ProgressCallback = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class ProgressContext:
    worker_name: str
    method: str
    args: list[Any]
    kwargs: dict[str, Any]
    started_at: float
    elapsed: float


ProgressProvider = Callable[[ProgressContext], Any]


@dataclass(slots=True)
class _InFlightRequest:
    method: str
    args: list[Any]
    kwargs: dict[str, Any]
    props: pika.BasicProperties
    delivery_tag: int | None
    started_at: float
    last_progress_at: float
    progress_interval: float
    progress_provider: ProgressProvider | None
    done: threading.Event = field(default_factory=threading.Event)
    response: dict[str, Any] | None = None
    client_gone: bool = False


def _normalize_progress_callback(fn: ProgressCallback) -> ProgressProvider:
    try:
        sig = signature(fn)
    except Exception:
        return lambda _ctx: fn()  # type: ignore[misc]

    if not sig.parameters:
        return lambda _ctx: fn()  # type: ignore[misc]
    return lambda ctx: fn(ctx)  # type: ignore[misc]


class TanukiWorker:
    def __init__(
        self,
        worker_name: str,
        config: RabbitMQConfig | None = None,
        *,
        worker_id: str | None = None,
    ) -> None:
        self._worker_name = worker_name
        self._config = config or RabbitMQConfig()
        self._worker_id = worker_id or f"tanuki-worker:{worker_name}"

        _, self._realm = self._config.split_worker_name(worker_name)
        self._request_exchange = self._config.request_exchange_name(worker_name)
        self._reply_exchange = self._config.reply_exchange_name(worker_name)
        self._routing_key = self._config.request_routing_key(worker_name)

        self._handlers: dict[str, Handler] = {}
        self._progress_handlers: dict[str, ProgressProvider] = {}
        self._progress_intervals: dict[str, float] = {}
        self.register("__tanuki_help__", self._tanuki_help)

        self._connection: pika.BlockingConnection | None = None
        self._consume_ch: pika.adapters.blocking_connection.BlockingChannel | None = None
        self._publish_ch: pika.adapters.blocking_connection.BlockingChannel | None = None
        self._queue_name: str | None = None
        self._stop_requested = False

    @property
    def config(self) -> RabbitMQConfig:
        return self._config

    @property
    def worker_name(self) -> str:
        return self._worker_name

    def handler(
        self,
        method: str,
        *,
        progress: ProgressCallback | None = None,
        progress_interval: float | None = None,
    ) -> Callable[[Handler], Handler]:
        def _decorator(fn: Handler) -> Handler:
            self._handlers[method] = fn
            if progress is not None:
                self.set_progress(method, progress, interval=progress_interval)
            return fn

        return _decorator

    def command(
        self,
        name: str,
        *,
        progress: ProgressCallback | None = None,
        progress_interval: float | None = None,
    ) -> Callable[[Handler], Handler]:
        return self.handler(name, progress=progress, progress_interval=progress_interval)

    def register(
        self,
        method: str,
        fn: Handler,
        *,
        progress: ProgressCallback | None = None,
        progress_interval: float | None = None,
    ) -> None:
        self._handlers[method] = fn
        if progress is not None:
            self.set_progress(method, progress, interval=progress_interval)

    def progress(self, method: str, *, interval: float | None = None) -> Callable[[ProgressCallback], ProgressCallback]:
        def _decorator(fn: ProgressCallback) -> ProgressCallback:
            self.set_progress(method, fn, interval=interval)
            return fn

        return _decorator

    def set_progress(self, method: str, fn: ProgressCallback | None, *, interval: float | None = None) -> None:
        if fn is None:
            self._progress_handlers.pop(method, None)
            self._progress_intervals.pop(method, None)
            return

        self._progress_handlers[method] = _normalize_progress_callback(fn)
        if interval is not None:
            self._progress_intervals[method] = float(interval)

    def _tanuki_help(self) -> dict[str, Any]:
        import inspect

        def _ann_to_str(ann: Any) -> str | None:
            if ann is inspect._empty:
                return None
            if isinstance(ann, type):
                return ann.__name__
            return str(ann)

        def _param_to_dict(p: Parameter) -> dict[str, Any]:
            return {
                "name": p.name,
                "kind": p.kind.name,
                "annotation": _ann_to_str(p.annotation),
                "has_default": p.default is not inspect._empty,
                "default": None if p.default is inspect._empty else repr(p.default),
            }

        commands: list[dict[str, Any]] = []
        for name, fn in sorted(self._handlers.items(), key=lambda kv: kv[0]):
            if name.startswith("__tanuki_"):
                continue
            try:
                sig: Signature = inspect.signature(fn)
                sig_str = f"{name}{sig}"
                params = [_param_to_dict(p) for p in sig.parameters.values()]
                return_ann = _ann_to_str(sig.return_annotation)
            except Exception:
                sig_str = name
                params = []
                return_ann = None

            doc = getattr(fn, "__doc__", None) or None
            if isinstance(doc, str):
                doc = doc.strip().splitlines()[0] if doc.strip() else None

            commands.append(
                {
                    "name": name,
                    "signature": sig_str,
                    "params": params,
                    "return": return_ann,
                    "doc": doc,
                }
            )

        return {
            "worker": self._worker_name,
            "realm": self._realm,
            "queue": self._config.request_queue_name(self._worker_name),
            "request_exchange": self._request_exchange,
            "reply_exchange": self._reply_exchange,
            "commands": commands,
        }

    def close(self) -> None:
        if self._consume_ch and self._consume_ch.is_open:
            try:
                self._consume_ch.close()
            except Exception:
                logger.debug("ignore close(consume_ch) error", exc_info=True)
        if self._publish_ch and self._publish_ch.is_open:
            try:
                self._publish_ch.close()
            except Exception:
                logger.debug("ignore close(publish_ch) error", exc_info=True)
        if self._connection and self._connection.is_open:
            try:
                self._connection.close()
            except Exception:
                logger.debug("ignore close(connection) error", exc_info=True)
        self._connection = None
        self._consume_ch = None
        self._publish_ch = None
        self._queue_name = None

    def stop(self) -> None:
        self._stop_requested = True
        self.close()

    def purge(self) -> int:
        self._ensure_connected()
        assert self._consume_ch and self._queue_name
        result = self._consume_ch.queue_purge(queue=self._queue_name)
        return int(result.method.message_count)

    def _ensure_connected(self) -> None:
        if self._connection and self._connection.is_open and self._consume_ch and self._publish_ch and self._queue_name:
            return

        self.close()

        self._connection = connect_blocking(self._config, connection_name=self._worker_id, max_retries=0)
        self._consume_ch = self._connection.channel()
        self._publish_ch = self._connection.channel()

        declare_rpc_topology(self._consume_ch, self._config, worker_name=self._worker_name)
        self._queue_name = declare_worker_queue(self._consume_ch, self._config, worker_name=self._worker_name)
        declare_rpc_topology(self._publish_ch, self._config, worker_name=self._worker_name)

        self._publish_ch.confirm_delivery()
        self._consume_ch.basic_qos(prefetch_count=self._config.prefetch_count)

    def _publish_reply(self, props: pika.BasicProperties, body: bytes, *, msg_type: str, warn_unroutable: bool) -> bool:
        if not props.reply_to:
            return False
        assert self._publish_ch is not None
        try:
            self._publish_ch.basic_publish(
                exchange=self._reply_exchange,
                routing_key=props.reply_to,
                body=body,
                properties=pika.BasicProperties(
                    content_type="application/json",
                    correlation_id=props.correlation_id,
                    app_id=self._worker_id,
                    type=msg_type,
                ),
                mandatory=True,
            )
            return True
        except (pika.exceptions.UnroutableError, pika.exceptions.NackError):
            if warn_unroutable:
                logger.warning("%s unroutable (client likely gone): reply_to=%s", msg_type, props.reply_to)
            else:
                logger.debug("%s unroutable (client likely gone): reply_to=%s", msg_type, props.reply_to)
            return False
        except pika.exceptions.AMQPError:
            logger.exception("failed to publish %s", msg_type)
            return False

    def _ack_if_needed(self, delivery_tag: int | None) -> None:
        if self._config.worker_auto_ack or delivery_tag is None:
            return
        assert self._consume_ch is not None
        try:
            self._consume_ch.basic_ack(delivery_tag=delivery_tag)
        except Exception:
            logger.debug("ignore ack error", exc_info=True)

    def _start_inflight(self, delivery_tag: int | None, props: pika.BasicProperties, body: bytes) -> _InFlightRequest | None:
        try:
            req = decode_json(body)
            method_name = str(req.get("method"))
            args = req.get("args") or []
            kwargs = req.get("kwargs") or {}
            if not isinstance(args, list) or not isinstance(kwargs, dict):
                raise ValueError("invalid request payload")

            fn = self._handlers.get(method_name)
            if fn is None:
                raise KeyError(f"unknown method: {method_name}")
        except KeyError as e:
            logger.warning(str(e))
            resp = build_error_response(e, include_traceback=self._config.include_traceback_in_error)
            self._publish_reply(props, encode_json(resp), msg_type="tanuki.response", warn_unroutable=True)
            self._ack_if_needed(delivery_tag)
            return None
        except Exception as e:
            logger.exception("failed to decode request")
            resp = build_error_response(e, include_traceback=self._config.include_traceback_in_error)
            self._publish_reply(props, encode_json(resp), msg_type="tanuki.response", warn_unroutable=True)
            self._ack_if_needed(delivery_tag)
            return None

        progress_provider = self._progress_handlers.get(method_name)
        progress_interval = float(self._progress_intervals.get(method_name, self._config.progress_interval))

        inflight = _InFlightRequest(
            method=method_name,
            args=args,
            kwargs=kwargs,
            props=props,
            delivery_tag=delivery_tag,
            started_at=time.monotonic(),
            last_progress_at=0.0,
            progress_interval=progress_interval,
            progress_provider=progress_provider,
        )

        def _run_handler() -> None:
            try:
                result = fn(*args, **kwargs)
                resp = build_ok_response(result)
            except KeyError as e:
                logger.warning(str(e))
                resp = build_error_response(e, include_traceback=self._config.include_traceback_in_error)
            except Exception as e:
                logger.exception("handler error")
                resp = build_error_response(e, include_traceback=self._config.include_traceback_in_error)
            inflight.response = resp
            inflight.done.set()

        threading.Thread(target=_run_handler, name=f"tanuki:{method_name}", daemon=True).start()
        return inflight

    def _maybe_send_progress(self, inflight: _InFlightRequest) -> None:
        if inflight.client_gone or inflight.progress_interval <= 0:
            return
        now = time.monotonic()
        if now - inflight.last_progress_at < inflight.progress_interval:
            return

        elapsed = now - inflight.started_at
        ctx = ProgressContext(
            worker_name=self._worker_name,
            method=inflight.method,
            args=inflight.args,
            kwargs=inflight.kwargs,
            started_at=inflight.started_at,
            elapsed=elapsed,
        )

        progress_payload: Any = {"status": "running"}
        if inflight.progress_provider is not None:
            try:
                progress_payload = inflight.progress_provider(ctx)
            except Exception:
                logger.exception("progress callback error; fallback to auto progress")
                inflight.progress_provider = None

        progress_msg = build_progress(progress_payload, elapsed=elapsed)
        try:
            progress_body = encode_json(progress_msg)
        except Exception:
            logger.exception("failed to serialize progress; fallback to auto progress")
            try:
                progress_body = encode_json(build_progress({"status": "running"}, elapsed=elapsed))
            except Exception:
                return

        if not inflight.props.reply_to:
            inflight.last_progress_at = now
            return

        ok = self._publish_reply(inflight.props, progress_body, msg_type="tanuki.progress", warn_unroutable=False)
        if not ok:
            inflight.client_gone = True
        inflight.last_progress_at = now

    def _finish_inflight(self, inflight: _InFlightRequest) -> None:
        resp = inflight.response or build_error_response(
            RuntimeError("missing response"),
            include_traceback=self._config.include_traceback_in_error,
        )
        try:
            resp_body = encode_json(resp)
        except Exception as e:
            logger.exception("failed to serialize response")
            resp_body = encode_json(build_error_response(e, include_traceback=self._config.include_traceback_in_error))

        if inflight.props.reply_to:
            self._publish_reply(inflight.props, resp_body, msg_type="tanuki.response", warn_unroutable=True)
        else:
            logger.debug("no reply_to set; dropping response")
        self._ack_if_needed(inflight.delivery_tag)

    def run(self, *, configure_logging: bool = True, log_level: int | str = "INFO") -> None:
        if configure_logging:
            _ensure_default_logging(log_level)

        startup_logged = False
        inflight: _InFlightRequest | None = None
        self._stop_requested = False

        while not self._stop_requested:
            try:
                self._ensure_connected()
                assert self._connection and self._consume_ch and self._queue_name

                if not startup_logged:
                    commands = sorted(k for k in self._handlers.keys() if not k.startswith("__tanuki_"))
                    cmd_str = ",".join(commands) if commands else "-"
                    realm = self._realm or "local"
                    if self._realm is None:
                        logger.info("TanukiWorker ready: %s (local) queue=%s cmds=%s", self._worker_name, self._queue_name, cmd_str)
                    else:
                        logger.info(
                            "TanukiWorker ready: %s (realm=%s) queue=%s req=%s rep=%s cmds=%s",
                            self._worker_name,
                            realm,
                            self._queue_name,
                            self._request_exchange,
                            self._reply_exchange,
                            cmd_str,
                        )
                    logger.debug(
                        "TanukiWorker connection: rabbitmq=%s:%s vhost=%s",
                        self._config.host,
                        self._config.port,
                        self._config.virtual_host,
                    )
                    startup_logged = True
                else:
                    logger.info("TanukiWorker reconnected: %s (realm=%s) queue=%s", self._worker_name, self._realm or "local", self._queue_name)

                while not self._stop_requested:
                    if inflight is None:
                        method_frame, props, body = self._consume_ch.basic_get(queue=self._queue_name, auto_ack=self._config.worker_auto_ack)
                        if method_frame is None:
                            self._connection.process_data_events(time_limit=1.0)
                            continue
                        delivery_tag = None if self._config.worker_auto_ack else int(method_frame.delivery_tag)
                        inflight = self._start_inflight(delivery_tag, props, body)
                        continue

                    if inflight.done.is_set():
                        self._finish_inflight(inflight)
                        inflight = None
                        continue

                    self._maybe_send_progress(inflight)
                    self._connection.process_data_events(time_limit=0.2)
            except KeyboardInterrupt:
                logger.info("TanukiWorker stopping (KeyboardInterrupt)")
                break
            except pika.exceptions.AMQPError:
                logger.exception("AMQP error; reconnecting soon")
                time.sleep(1.0)
            finally:
                self.close()

    def start(self, *, configure_logging: bool = True, log_level: int | str = "INFO") -> None:
        self.run(configure_logging=configure_logging, log_level=log_level)


def _coerce_log_level(level: int | str) -> int:
    if isinstance(level, int):
        return level
    name = level.strip().upper()
    mapping = logging.getLevelNamesMapping()
    if name not in mapping:
        raise ValueError(f"unknown log level: {level!r}")
    return int(mapping[name])


def _ensure_default_logging(level: int | str) -> None:
    target_level = _coerce_log_level(level)
    logging.getLogger("tanu").setLevel(target_level)

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    logging.basicConfig(
        level=target_level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Silence noisy pika internals by default (opt-in via user logging config).
    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("pika.adapters.blocking_connection").setLevel(logging.WARNING)
    logging.getLogger("pika.adapters.utils.connection_workflow").setLevel(logging.CRITICAL)
    logging.getLogger("pika.adapters.utils.io_services_utils").setLevel(logging.CRITICAL)
