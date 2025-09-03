from module.i18n.services.i18n_manager import I18nManager

_i18n_manager = None

def get_i18n_manager() -> I18nManager:
    """获取全局i18n管理器实例"""
    global _i18n_manager
    if _i18n_manager is None:
        _i18n_manager = I18nManager()
    return _i18n_manager

__all__ = ['get_i18n_manager', 'I18nManager']