import enum
import json
import os
import traceback
from abc import ABC
from time import sleep

import zmq
import zmq.asyncio
from loguru import logger

from aitrados_api.common_lib.common import run_asynchronous_function
from aitrados_api.common_lib.run_utils import *
from aitrados_api.trade_middleware.request import FrontendRequest
from aitrados_api.trade_middleware.trade_middleware_utils import set_pubsub_heartbeat_options
from aitrados_api.trade_middleware.client_adresss_detector import PubAddressDetector


class AsyncSubscriberMixin(ABC):
    def __init__(self,host:str=None,secret_key:str=None):
        self.ctx = None
        self.socket = None
        self.host=host
        self.secret_key=secret_key

    @classmethod
    def check_secret_key(cls,host:str=None,secret_key:str=None):
        if not host:
            host = os.getenv("MIDDLEWARE_HOST", None)
        if not host:
            return True
        if not secret_key:
            secret_key=os.getenv("AITRADOS_SECRET_KEY",'')
        from aitrados_api.trade_middleware_service.trade_middleware_identity import aitrados_api_identity as idt
        try:
            result = FrontendRequest.call_sync(
                idt.backend_identity,
                "get_all_online_backend_services",


                timeout=5,# 单位秒
                secret_key=secret_key,
                host=host
            )
            if result["status"]=="invalid_secret_key":
                logger.error(result["message"])
                return False
            return True
        except:
            return True
    @classmethod
    def _deserialize_response(cls, response: bytes) -> Any:
        try:
            return json.loads(response.decode('utf-8'))
        except:
            return response.decode('utf-8')
    def _instance(self):
        self.ctx = zmq.asyncio.Context()
        self.socket = self.ctx.socket(zmq.SUB)

        set_pubsub_heartbeat_options(self.socket)
        self.addr = PubAddressDetector.get_cached_type()

        self.socket.connect(self.addr)

    def unsubscribe_topics(self, *topics):
        if self.check_secret_key(self.host,self.secret_key)==False:
            return
        if not self.socket or not self.ctx:
            return
        for topic in topics:
            if isinstance(topic, str):
                topic = topic.encode()
            elif isinstance(topic, enum.Enum):
                topic = topic.value
            elif not isinstance(topic, bytes):
                raise TypeError(f"Invalid topic type: {type(topic)}")
            self.socket.setsockopt(zmq.UNSUBSCRIBE, topic)

    def subscribe_topics(self, *topics):
        if self.check_secret_key(self.host,self.secret_key)==False:
            return
        if not self.socket or not self.ctx:
            self._instance()

        for topic in topics:
            if isinstance(topic, str):
                topic = topic.encode()
            elif isinstance(topic, enum.Enum):
                topic = topic.value
            elif not isinstance(topic, bytes):
                logger.warning(f"Invalid topic type {topic}: {type(topic)}")
                return
            self.socket.setsockopt(zmq.SUBSCRIBE, topic)


    async def __run(self):
        if not self.socket or not self.ctx:
            self._instance()
        try:
            while True:
                receive_data = await self.socket.recv_multipart()
                if len(receive_data)<2:
                    continue

                topic, msg=receive_data[-2],receive_data[-1]
                topic_str = topic.decode()
                if not topic_str:
                    continue

                if not (msg:=self._deserialize_response(msg)):
                    continue
                '''
                if len(receive_data) > 2:
                    print("Length exceeds 2", receive_data)
                if isinstance(msg, str):
                    print("Abnormal value", topic_str, msg)
                    print("Abnormal data,", receive_data)
                '''
                if any_function := getattr(self, topic_str, None):
                    try:
                        await ExecuteCallback.arun_background(any_function, msg)
                    except Exception as e:
                        traceback.print_exc()


        except KeyboardInterrupt:
            print("[Subscriber] Interrupted.")
        except Exception as e:
            traceback.print_exc()
            print(f"[Subscriber] Error: {e}")
        finally:
            self.socket.close(linger=0)
            self.ctx.term()
    def __send_null_msg(self):
        """
        Send an empty message to tell the middleware that I am online.
        The problem of not receiving the first message has been resolved.
        """
        from aitrados_api.trade_middleware.publisher import async_publisher_instance
        sleep(0.1)
        async_publisher_instance.send_topic("null", "null")
    def run(self, is_thread=True):
        if not is_thread:
            run_asynchronous_function(self.__run())
        else:
            threading.Thread(target=lambda: run_asynchronous_function(self.__run()), daemon=True).start()
        threading.Thread(target=self.__send_null_msg, daemon=True).start()