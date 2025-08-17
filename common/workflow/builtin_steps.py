"""
内置步骤实现 - 继续实现剩余的内置步骤
"""
from utils.logging.logger import logger


def builtin_fill_input_step(client=None, context=None, selector=None, value=None, **kwargs):
    """内置填写输入框步骤"""
    try:
        if not client or not hasattr(client, 'page'):
            logger.error("Web客户端未初始化")
            return False
        
        page = client.page
        page.wait_for_selector(selector, timeout=10000)
        page.fill(selector, str(value))
        
        context[f'filled_{selector}'] = value
        logger.info(f"填写输入框步骤执行成功: {selector}")
        return True
        
    except Exception as e:
        logger.error(f"填写输入框步骤异常: {e}")
        return False


def builtin_verify_element_step(client=None, context=None, selector=None, **kwargs):
    """内置验证元素步骤"""
    try:
        if not client or not hasattr(client, 'page'):
            logger.error("Web客户端未初始化")
            return False
        
        page = client.page
        is_visible = page.is_visible(selector)
        
        if is_visible:
            context[f'verified_{selector}'] = True
            logger.info(f"验证元素步骤执行成功: {selector}")
            return True
        else:
            logger.error(f"验证元素步骤失败: {selector} 不可见")
            return False
            
    except Exception as e:
        logger.error(f"验证元素步骤异常: {e}")
        return False


def builtin_verify_url_step(client=None, context=None, pattern=None, **kwargs):
    """内置验证URL步骤"""
    try:
        if not client or not hasattr(client, 'page'):
            logger.error("Web客户端未初始化")
            return False
        
        page = client.page
        current_url = page.url
        
        import fnmatch
        if fnmatch.fnmatch(current_url, pattern):
            context['verified_url'] = current_url
            logger.info(f"验证URL步骤执行成功: {current_url} 匹配 {pattern}")
            return True
        else:
            logger.error(f"验证URL步骤失败: {current_url} 不匹配 {pattern}")
            return False
            
    except Exception as e:
        logger.error(f"验证URL步骤异常: {e}")
        return False


def builtin_verify_api_response_step(client=None, context=None, endpoint=None, expected_status=200, **kwargs):
    """内置验证API响应步骤"""
    try:
        if not client:
            logger.error("API客户端未初始化")
            return False
        
        response = client.get(endpoint)
        
        if response.status_code == expected_status:
            context[f'verified_api_{endpoint}'] = response.status_code
            logger.info(f"验证API响应步骤执行成功: {endpoint}")
            return True
        else:
            logger.error(f"验证API响应步骤失败: {endpoint} 返回 {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"验证API响应步骤异常: {e}")
        return False


def builtin_wait_for_element_step(client=None, context=None, selector=None, timeout=10000, **kwargs):
    """内置等待元素步骤"""
    try:
        if not client or not hasattr(client, 'page'):
            logger.error("Web客户端未初始化")
            return False
        
        page = client.page
        page.wait_for_selector(selector, timeout=timeout)
        
        context[f'waited_{selector}'] = True
        logger.info(f"等待元素步骤执行成功: {selector}")
        return True
        
    except Exception as e:
        logger.error(f"等待元素步骤异常: {e}")
        return False


def builtin_wait_for_url_step(client=None, context=None, pattern=None, timeout=10000, **kwargs):
    """内置等待URL步骤"""
    try:
        if not client or not hasattr(client, 'page'):
            logger.error("Web客户端未初始化")
            return False
        
        page = client.page
        page.wait_for_url(pattern, timeout=timeout)
        
        context['waited_url'] = page.url
        logger.info(f"等待URL步骤执行成功: {pattern}")
        return True
        
    except Exception as e:
        logger.error(f"等待URL步骤异常: {e}")
        return False


def builtin_api_set_context_step(client=None, context=None, context_data=None, **kwargs):
    """内置API设置上下文步骤"""
    try:
        if not client:
            logger.error("API客户端未初始化")
            return False
        
        # 设置API上下文
        response = client.post('/api/context', json=context_data)
        
        if response.status_code == 200:
            context['api_context_set'] = True
            logger.info("API设置上下文步骤执行成功")
            return True
        else:
            logger.error(f"API设置上下文步骤失败: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"API设置上下文步骤异常: {e}")
        return False


def builtin_custom_action_step(client=None, context=None, action_func=None, **kwargs):
    """内置自定义动作步骤"""
    try:
        if not action_func:
            logger.error("未提供自定义动作函数")
            return False
        
        # 执行自定义动作
        result = action_func(client=client, context=context, **kwargs)
        
        if result:
            context['custom_action_executed'] = True
            logger.info("自定义动作步骤执行成功")
            return True
        else:
            logger.error("自定义动作步骤执行失败")
            return False
            
    except Exception as e:
        logger.error(f"自定义动作步骤异常: {e}")
        return False


# 步骤注册映射
BUILTIN_STEPS = {
    'fill_input': builtin_fill_input_step,
    'verify_element': builtin_verify_element_step,
    'verify_url': builtin_verify_url_step,
    'verify_api_response': builtin_verify_api_response_step,
    'wait_for_element': builtin_wait_for_element_step,
    'wait_for_url': builtin_wait_for_url_step,
    'api_set_context': builtin_api_set_context_step,
    'custom_action': builtin_custom_action_step
}
