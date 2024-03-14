import logging
import time
import traceback

from deepdiff import DeepDiff
from pydantic import BaseModel

from hummingbot.core.data_type.common import (
    LPType,
    OpenOrder,
    OrderType,
    PositionAction,
    PositionMode,
    PositionSide,
    PriceType,
    TradeType,
)
from hummingbot.smart_components.utils.config_encoder_decoder import ConfigEncoderDecoder

logger = logging.getLogger()

"""
for dynamic reload value from yml config when set config_file attributes
encoder_decoder = ConfigEncoderDecoder()
rows = encoder_decoder.yaml_load(f"xxx.yml")
rows["config_file"] = f"xxx.yml"
ReloadableBase(**rows).reload()
"""


class ReloadableBase(BaseModel):
    refresh_time: int = 60 * 5
    config_file: str = None
    config_file_last_reload: int = 0

    def reload(self):
        try:
            if self.config_file_last_reload == 0:
                self.config_file_last_reload = time.time()
                return

            t = self.config_file_last_reload + self.refresh_time
            if self.config_file and t <= time.time():
                logger.info(
                    "reload model {class_name} from config file {config_file} interval on {interval}".format(
                        class_name=self.__class__, config_file=self.config_file, interval=self.refresh_time))
                ed = ConfigEncoderDecoder(OrderType, PositionMode, TradeType, OpenOrder,
                                          PositionAction, PositionSide, PriceType, LPType)
                rws = ed.yaml_load(self.config_file)
                rws['config_file'] = self.config_file
                rws['refresh_time'] = self.refresh_time
                rws['config_file_last_reload'] = self.config_file_last_reload
                instance = self.__class__(**rws)
                differ = DeepDiff(self.dict(), rws, ignore_order=True)
                if differ:
                    logger.info("reload model {class_name} from config file {config_file} got diff:{differ}".format(
                        class_name=self.__class__, config_file=self.config_file, differ=differ))

                self.__dict__.update(instance.__dict__)
                self.config_file_last_reload = time.time()
        except Exception as e:
            traceback.print_exc()
            logger.error("reload model {class_name} from config file {config_file} error".format(
                class_name=self.__class__, config_file=self.config_file))
            logger.error(e)
