# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from biotmed_settings_sdk.api.backup_api_api import BackupAPIApi
    from biotmed_settings_sdk.api.code_snippet_api_api import CodeSnippetAPIApi
    from biotmed_settings_sdk.api.entity_api_api import EntityAPIApi
    from biotmed_settings_sdk.api.export_import_configuration_api_api import ExportImportConfigurationAPIApi
    from biotmed_settings_sdk.api.health_check_api_api import HealthCheckAPIApi
    from biotmed_settings_sdk.api.interception_configuration_api_api import InterceptionConfigurationAPIApi
    from biotmed_settings_sdk.api.locale_api_api import LocaleAPIApi
    from biotmed_settings_sdk.api.plugin_v2_api_api import PluginV2APIApi
    from biotmed_settings_sdk.api.system_api_api import SystemAPIApi
    from biotmed_settings_sdk.api.template_api_api import TemplateAPIApi
    from biotmed_settings_sdk.api.translation_api_api import TranslationAPIApi
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from biotmed_settings_sdk.api.backup_api_api import BackupAPIApi
from biotmed_settings_sdk.api.code_snippet_api_api import CodeSnippetAPIApi
from biotmed_settings_sdk.api.entity_api_api import EntityAPIApi
from biotmed_settings_sdk.api.export_import_configuration_api_api import ExportImportConfigurationAPIApi
from biotmed_settings_sdk.api.health_check_api_api import HealthCheckAPIApi
from biotmed_settings_sdk.api.interception_configuration_api_api import InterceptionConfigurationAPIApi
from biotmed_settings_sdk.api.locale_api_api import LocaleAPIApi
from biotmed_settings_sdk.api.plugin_v2_api_api import PluginV2APIApi
from biotmed_settings_sdk.api.system_api_api import SystemAPIApi
from biotmed_settings_sdk.api.template_api_api import TemplateAPIApi
from biotmed_settings_sdk.api.translation_api_api import TranslationAPIApi

""",
            name=__name__,
            doc=__doc__,
        )
    )
