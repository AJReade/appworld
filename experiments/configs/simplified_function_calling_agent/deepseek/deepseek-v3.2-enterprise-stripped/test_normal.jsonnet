local experiment_prompts_path = std.extVar("APPWORLD_EXPERIMENT_PROMPTS_PATH");
local experiment_configs_path = std.extVar("APPWORLD_EXPERIMENT_CONFIGS_PATH");
local experiment_code_path = std.extVar("APPWORLD_EXPERIMENT_CODE_PATH");
local model_config = {
    "client_name": "openai",
    "api_type": "chat_completions",
    "base_url": "https://api.deepseek.com/v1",
    "api_key_env_name": "DEEPSEEK_API_KEY",
    "name": "deepseek-chat",
    "temperature": 1.0,
    "seed": 100,
    "drop_reasoning_content": false,
    "cost_per_token": {"input_cache_hit": 2.8e-08, "input_cache_miss": 2.8e-07, "input_cache_write": 0.0, "output": 4.2e-07},
    "retry_after_n_seconds": 15,
    "use_cache": false,
    "max_retries": 100,
};
{
    "type": "simplified",
    "config": {
        "agent": {
            "type": "enterprise_function_calling",
            "model_config": model_config + {
                "tool_choice": "auto",
                "parallel_tool_calls": true,
            },
            "role_apps": ["api_docs", "supervisor", "phone", "venmo", "splitwise", "amazon"],
            "role_description": "You are a personal finance assistant. Your job is to manage payments, friend lists, expenses, and shopping.",
            "appworld_config": {
                "random_seed": 100,
                "raise_on_extra_parameters": true,
                "include_direct_functions": true,
                "direct_function_separator": "__",
            },
            "logger_config": {
                "color": true,
                "verbose": true,
            },
            "usage_tracker_config": {
                "max_cost_overall": 1000,
                "max_cost_per_task": 10,
                "max_output_tokens_per_task": 100000,
            },
            "prompt_file_path": experiment_prompts_path + "/enterprise_agent/instructions.txt",
            "max_steps": 50,
            "log_lm_calls": true,
            "skip_if_finished": true,
        },
        "dataset": "test_normal",
    },
    "metadata": {
        "model": {
            "file_name": "deepseek-v3.2-enterprise-stripped",
            "humanized_name": "DeepSeek V3.2 Enterprise Stripped (Personal Finance)",
            "precise_name": "deepseek-chat",
            "creator": "deepseek",
            "provider": "deepseek",
        },
        "agent": {
            "file_name": "simplified_function_calling_agent",
            "humanized_name": "Enterprise Function Calling Agent",
        },
    },
}
