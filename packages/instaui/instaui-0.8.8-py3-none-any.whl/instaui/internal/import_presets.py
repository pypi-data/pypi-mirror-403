"""
Preset modules and factory functions for quick usage.
"""

from typing import Optional
from instaui.constants.ui import (
    STORAGE_REF_METHOD,
    INSTAUI_JS_MODULE_NAME,
    USE_DARK_REF_METHOD,
    USE_LANGUAGE_METHOD,
)
from instaui.systems.dataclass_system import dataclass


@dataclass()
class ImportItem:
    module_name: str
    member_name: str
    member_alias: Optional[str] = None


class Vue:
    """
    Preset factory for Vue imports.

    Usage:
        Vue.ref()                (module='vue', name='ref')
        Vue.ref(alias="r")       (module='vue', name='ref', alias='r')
        Vue.reactive()           (module='vue', name='reactive')
    """

    module_name = "vue"

    @staticmethod
    def ref(alias: Optional[str] = None):
        return ImportItem(
            module_name=Vue.module_name,
            member_name="ref",
            member_alias=alias,
        )

    @staticmethod
    def to_refs(alias: Optional[str] = None):
        return ImportItem(
            module_name=Vue.module_name,
            member_name="toRefs",
            member_alias=alias,
        )

    @staticmethod
    def on_mounted():
        return ImportItem(
            module_name=Vue.module_name,
            member_name="onMounted",
        )


class Instaui:
    """
    Preset factory for Instaui imports.
    """

    module_name = INSTAUI_JS_MODULE_NAME

    @staticmethod
    def install():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="install",
        )

    @staticmethod
    def inject():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="inject",
        )

    @staticmethod
    def provide():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="provide",
        )

    @staticmethod
    def ref():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="createRef",
            member_alias="cref",
        )

    @staticmethod
    def render_component():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="renderComponent",
            member_alias="rh",
        )

    @staticmethod
    def render_scope():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="renderScope",
            member_alias="rs",
        )

    @staticmethod
    def render_content():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="content",
            member_alias="rc",
        )

    @staticmethod
    def storage_ref():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name=STORAGE_REF_METHOD,
        )

    @staticmethod
    def use_dark_ref():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name=USE_DARK_REF_METHOD,
        )

    @staticmethod
    def use_language_ref():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name=USE_LANGUAGE_METHOD,
        )

    @staticmethod
    def use_page_title_ref():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="usePageTitleRef",
        )

    @staticmethod
    def web_computed_ref():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="createWebComputedRef",
            member_alias="webCp",
        )

    @staticmethod
    def web_event():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="createWebEvent",
            member_alias="webEvt",
        )

    @staticmethod
    def js_event():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="createJsEvent",
            member_alias="jsEvt",
        )

    @staticmethod
    def expr_event():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="createExprEvent",
            member_alias="exprEvt",
        )

    @staticmethod
    def web_watch_task_scheduler():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="webWatchTaskScheduler",
            member_alias="wts",
        )

    @staticmethod
    def vfor():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="genVFor",
            member_alias="vfor",
        )

    @staticmethod
    def match():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="match",
        )

    @staticmethod
    def vif():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="vif",
        )

    @staticmethod
    def track_path():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="trackPath",
            member_alias="tp",
        )

    @staticmethod
    def js_computed():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="createJsComputed",
            member_alias="jsCp",
        )

    @staticmethod
    def expr_computed():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="createExprComputed",
            member_alias="exprCp",
        )

    @staticmethod
    def js_watch():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="jsWatch",
            member_alias="jws",
        )

    @staticmethod
    def expr_watch():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="exprWatch",
            member_alias="ews",
        )

    @staticmethod
    def str_format():
        return ImportItem(
            module_name=Instaui.module_name,
            member_name="strFormat",
            member_alias="sf",
        )

    @staticmethod
    def to_value():
        return ImportItem(module_name=Instaui.module_name, member_name="toValue")
