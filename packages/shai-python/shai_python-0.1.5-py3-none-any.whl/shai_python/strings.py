"""
Internationalization module for Shai
Automatically detects system language and provides appropriate translations
"""

import locale
import os


class Translator:
    """Simple translator class for internationalization"""

    def __init__(self):
        self.language = self.detect_language()
        self.translations = self.load_translations()

    def detect_language(self) -> str:
        """Detect system language preference"""
        # Check environment variables first
        lang_env = os.environ.get('LANG', '').lower()
        lc_all = os.environ.get('LC_ALL', '').lower()
        lc_messages = os.environ.get('LC_MESSAGES', '').lower()

        # Check for Chinese language indicators
        chinese_indicators = ['zh_cn', 'zh_tw', 'zh_hk', 'zh_sg', 'zh']

        for env_var in [lang_env, lc_all, lc_messages]:
            for indicator in chinese_indicators:
                if indicator in env_var:
                    return 'zh'

        # Check system locale
        try:
            system_locale = locale.getlocale()[0]
            if system_locale and any(indicator in system_locale.lower() for indicator in chinese_indicators):
                return 'zh'
        except:
            pass
        # Default to English
        return 'en'

    def load_translations(self) -> dict[str, dict[str, str]]:
        """Load translation strings"""
        return {
            'en': {
                # Loading messages
                'thinking': 'Thinking...',

                # Command execution
                'dangerous_pattern_detected': 'Dangerous command pattern detected: {command}',
                'confirm_dangerous_command': 'Are you sure you want to execute this dangerous command? (YES/no): ',
                'dangerous_command_cancelled': 'Dangerous command cancelled.',
                'command_execution_failed': 'Command execution failed, exit code: {exit_code}',
                'error_message': 'Error message:',
                # Shell command display
                'risk_level_prompt': 'This command has a risk level of {risk_level}, still execute? (YES/no): ',
                'execute_prompt': '[{risk_level}]Execute this command? (y/N): ',
                'command_not_executed': 'Command not executed.',
                # Configuration
                'config_init_error': 'Error initializing config: {error}',
                'config_file_missing': 'Configuration file missing.',
                'config_edit_explanation': "This command will open the configuration file with your default editor.\nYou need to configure the provider's API key and related parameters here so the program can properly call the model interface.\nYou can always display this command with {yellow_shai_config}.",
                # Errors
                'error': 'Error: {error}',
                'model_not_found': 'Model not found: {model_name}',
                'provider_not_configured': 'Provider not configured: {provider_name}',
                'env_var_not_defined': 'Environment variable not defined: {var_name}',
                'task_description_empty': 'Task description cannot be empty',
            },
            'zh': {
                # Loading messages
                'thinking': '思考中...',

                # Command execution
                'dangerous_pattern_detected': '检测到危险命令模式: {command}',
                'confirm_dangerous_command': '确定要执行这个危险命令吗？(YES/no): ',
                'dangerous_command_cancelled': '危险命令已取消。',
                'command_execution_failed': '命令执行失败，错误码: {exit_code}',
                'error_message': '错误信息:',
                # Shell command display
                'risk_level_prompt': '此命令的风险等级为 {risk_level}，仍然执行吗？(YES/no): ',
                'execute_prompt': '[{risk_level}]执行此命令？(y/N): ',
                'command_not_executed': '命令未执行。',
                # Configuration
                'config_init_error': '配置文件错误: {error}',
                'config_file_missing': '配置文件不存在',
                'config_edit_explanation': "该命令将使用默认编辑器打开配置文件。\n配置服务商的api key及相关参数，以便程序能够正常调用模型接口。\n任何时候可以通过{yellow_shai_config}显示此命令。",
                # Errors
                'error': '错误: {error}',
                'model_not_found': '找不到模型: {model_name}',
                'provider_not_configured': '未配置Provider: {provider_name}',
                'env_var_not_defined': '未定义环境变量: {var_name}',
                'task_description_empty': '任务描述不能为空',
            }
        }

    def get(self, key: str, **kwargs) -> str:
        """Get translated string with formatting"""
        translation = self.translations[self.language].get(key, key)

        # Format the string if there are kwargs
        if kwargs:
            try:
                return translation.format(**kwargs)
            except KeyError:
                # If formatting fails, return the translation as-is
                return translation

        return translation

    def __call__(self, key: str, **kwargs) -> str:
        """Make the translator callable"""
        return self.get(key, **kwargs)


# Create global translator instance
_ = Translator()


def get_translator() -> Translator:
    """Get the global translator instance"""
    return _