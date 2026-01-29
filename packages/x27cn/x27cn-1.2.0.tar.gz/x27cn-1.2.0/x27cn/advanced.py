"""
X27CN 高级代码混淆模块
提供深层混淆功能，使代码难以被AI识别和分析
"""

import re
import random
import string
import hashlib
from typing import List, Dict, Set, Tuple

class JSObfuscator:
    """JavaScript 代码混淆器"""
    
    # JavaScript 保留关键字（不能混淆）
    RESERVED_WORDS = {
        'break', 'case', 'catch', 'continue', 'debugger', 'default', 'delete',
        'do', 'else', 'finally', 'for', 'function', 'if', 'in', 'instanceof',
        'new', 'return', 'switch', 'this', 'throw', 'try', 'typeof', 'var',
        'void', 'while', 'with', 'class', 'const', 'enum', 'export', 'extends',
        'import', 'super', 'implements', 'interface', 'let', 'package', 'private',
        'protected', 'public', 'static', 'yield', 'true', 'false', 'null',
        'undefined', 'NaN', 'Infinity', 'arguments', 'eval', 'async', 'await',
        'of', 'get', 'set'
    }
    
    # 常见的 JSON 字段名和 API 字段（不能混淆，保持语义）
    JSON_FIELDS = {
        'status', 'version', 'colo', 'host', 'uuid', 'vless', 'two_proxy',
        'error', 'message', 'success', 'data', 'result', 'code', 'msg',
        'default', 'hk', 'env', 'current', 'options', 'name', 'address',
        'new_ip', 'is_default_uuid', 'two_proxy_enabled', 'two_proxy_host',
        'two_proxy_port', 'hostname', 'port', 'username', 'password',
        'enabled', 'global', 'account', 'local', 'randomIP', 'randomcount',
        'specPort', 'SUBNAME', 'SUBUpdateTime', 'TOKEN', 'SUBAPI', 'SUBCONFIG',
        'SUBEMOJI', 'PROXYIP', 'SOCKS5', 'whiteList', 'BotToken', 'ChatID',
        'Email', 'GlobalAPIKey', 'AccountID', 'APIToken', 'UsageAPI', 'Usage',
        'pages', 'workers', 'total', 'max', 'init', 'loadTime', 'plaintext',
        'key', 'Content-Type', 'X-Encrypted', 'X-Key-Hint'
    }
    
    # 常见的内置对象和方法（不能混淆）
    BUILTIN_OBJECTS = {
        'console', 'window', 'document', 'navigator', 'location', 'history',
        'localStorage', 'sessionStorage', 'JSON', 'Math', 'Date', 'Array',
        'Object', 'String', 'Number', 'Boolean', 'RegExp', 'Error', 'Promise',
        'Map', 'Set', 'Symbol', 'Proxy', 'Reflect', 'WeakMap', 'WeakSet',
        'ArrayBuffer', 'DataView', 'Int8Array', 'Uint8Array', 'Uint8ClampedArray',
        'Int16Array', 'Uint16Array', 'Int32Array', 'Uint32Array', 'Float32Array',
        'Float64Array', 'BigInt64Array', 'BigUint64Array', 'TextEncoder', 'TextDecoder',
        'fetch', 'Request', 'Response', 'Headers', 'URL', 'URLSearchParams',
        'WebSocket', 'XMLHttpRequest', 'FormData', 'Blob', 'File', 'FileReader',
        'crypto', 'atob', 'btoa', 'setTimeout', 'setInterval', 'clearTimeout',
        'clearInterval', 'requestAnimationFrame', 'cancelAnimationFrame',
        'alert', 'confirm', 'prompt', 'open', 'close', 'print', 'addEventListener',
        'removeEventListener', 'dispatchEvent', 'createElement', 'getElementById',
        'getElementsByClassName', 'getElementsByTagName', 'querySelector',
        'querySelectorAll', 'appendChild', 'removeChild', 'insertBefore',
        'replaceChild', 'getAttribute', 'setAttribute', 'removeAttribute',
        'hasAttribute', 'classList', 'style', 'innerHTML', 'textContent',
        'value', 'checked', 'selected', 'disabled', 'href', 'src', 'id', 'name',
        'type', 'target', 'length', 'prototype', 'constructor', 'toString',
        'valueOf', 'hasOwnProperty', 'isPrototypeOf', 'propertyIsEnumerable',
        'apply', 'call', 'bind', 'push', 'pop', 'shift', 'unshift', 'splice',
        'slice', 'concat', 'join', 'reverse', 'sort', 'filter', 'map', 'reduce',
        'reduceRight', 'every', 'some', 'find', 'findIndex', 'includes', 'indexOf',
        'lastIndexOf', 'forEach', 'keys', 'values', 'entries', 'from', 'isArray',
        'parse', 'stringify', 'log', 'warn', 'error', 'info', 'debug', 'table',
        'time', 'timeEnd', 'trace', 'assert', 'count', 'group', 'groupEnd',
        'floor', 'ceil', 'round', 'abs', 'min', 'max', 'pow', 'sqrt', 'random',
        'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'atan2', 'exp', 'log',
        'now', 'getTime', 'getFullYear', 'getMonth', 'getDate', 'getDay',
        'getHours', 'getMinutes', 'getSeconds', 'getMilliseconds', 'setTime',
        'charCodeAt', 'charAt', 'substring', 'substr', 'split', 'replace',
        'match', 'search', 'toLowerCase', 'toUpperCase', 'trim', 'padStart',
        'padEnd', 'startsWith', 'endsWith', 'repeat', 'test', 'exec',
        'then', 'catch', 'finally', 'resolve', 'reject', 'all', 'race', 'any',
        'allSettled', 'assign', 'freeze', 'seal', 'defineProperty', 'getOwnPropertyDescriptor',
        'getOwnPropertyNames', 'getPrototypeOf', 'setPrototypeOf', 'create',
        'env', 'connect', 'upgrade', 'headers', 'body', 'method', 'url', 'status',
        'statusText', 'ok', 'redirected', 'text', 'json', 'blob', 'arrayBuffer',
        'formData', 'clone', 'send', 'accept', 'write', 'close', 'readable',
        'writable', 'getReader', 'getWriter', 'read', 'releaseLock', 'cancel',
        'abort', 'signal', 'reason', 'throwIfAborted', 'addEventListener',
        'removeEventListener', 'dispatchEvent', 'onmessage', 'onerror', 'onopen',
        'onclose', 'readyState', 'bufferedAmount', 'extensions', 'protocol',
        'binaryType', 'CONNECTING', 'OPEN', 'CLOSING', 'CLOSED', 'byteLength',
        'byteOffset', 'buffer', 'BYTES_PER_ELEMENT', 'subarray', 'set', 'fill',
        'copyWithin', 'getInt8', 'getUint8', 'getInt16', 'getUint16', 'getInt32',
        'getUint32', 'getFloat32', 'getFloat64', 'getBigInt64', 'getBigUint64',
        'setInt8', 'setUint8', 'setInt16', 'setUint16', 'setInt32', 'setUint32',
        'setFloat32', 'setFloat64', 'setBigInt64', 'setBigUint64', 'decode',
        'encode', 'digest', 'subtle', 'getRandomValues', 'randomUUID'
    }
    
    def __init__(self, seed: str = None):
        """初始化混淆器"""
        self.seed = seed or str(random.random())
        random.seed(self.seed)
        self.name_map: Dict[str, str] = {}
        self.string_array: List[str] = []
        self.counter = 0
        
    def _generate_name(self, length: int = 6) -> str:
        """生成混淆的变量名"""
        # 使用 _0x 前缀 + 十六进制格式，模仿常见混淆器风格
        self.counter += 1
        hex_part = hashlib.md5(f"{self.seed}{self.counter}".encode()).hexdigest()[:length]
        return f"_0x{hex_part}"
    
    def _generate_hex_name(self) -> str:
        """生成纯十六进制样式的变量名"""
        self.counter += 1
        return f"_0x{self.counter:04x}"
    
    def _string_to_hex_escape(self, s: str) -> str:
        """将字符串转换为十六进制转义序列"""
        result = []
        for char in s:
            code = ord(char)
            if code < 256:
                result.append(f"\\x{code:02x}")
            else:
                result.append(f"\\u{code:04x}")
        return ''.join(result)
    
    def _string_to_charcode_array(self, s: str) -> str:
        """将字符串转换为 String.fromCharCode 调用"""
        codes = [str(ord(c)) for c in s]
        return f"String.fromCharCode({','.join(codes)})"
    
    def _string_to_split_concat(self, s: str) -> str:
        """将字符串拆分并用加法连接"""
        if len(s) <= 2:
            return f'"{self._string_to_hex_escape(s)}"'
        
        # 随机拆分点
        parts = []
        i = 0
        while i < len(s):
            chunk_size = random.randint(1, 3)
            chunk = s[i:i + chunk_size]
            parts.append(f'"{self._string_to_hex_escape(chunk)}"')
            i += chunk_size
        
        return '+'.join(parts)
    
    def _encode_string(self, s: str, method: str = 'random') -> str:
        """使用指定方法编码字符串"""
        if method == 'random':
            method = random.choice(['hex', 'charcode', 'split', 'array'])
        
        if method == 'hex':
            return f'"{self._string_to_hex_escape(s)}"'
        elif method == 'charcode':
            return self._string_to_charcode_array(s)
        elif method == 'split':
            return self._string_to_split_concat(s)
        elif method == 'array':
            # 添加到字符串数组，返回数组访问
            if s not in self.string_array:
                self.string_array.append(s)
            idx = self.string_array.index(s)
            return f"_0xstr[{idx}]"
        else:
            return f'"{self._string_to_hex_escape(s)}"'
    
    def _extract_identifiers(self, code: str) -> Set[str]:
        """提取代码中的标识符（包括中文变量名）"""
        # 匹配变量声明（支持中文）
        var_pattern = r'\b(?:var|let|const)\s+([\u4e00-\u9fa5a-zA-Z_$][\u4e00-\u9fa5a-zA-Z0-9_$]*)'
        # 匹配函数声明（支持中文）
        func_pattern = r'\bfunction\s+([\u4e00-\u9fa5a-zA-Z_$][\u4e00-\u9fa5a-zA-Z0-9_$]*)'
        # 匹配箭头函数参数
        arrow_pattern = r'\(([\u4e00-\u9fa5a-zA-Z_$][\u4e00-\u9fa5a-zA-Z0-9_$]*(?:\s*,\s*[\u4e00-\u9fa5a-zA-Z_$][\u4e00-\u9fa5a-zA-Z0-9_$]*)*)\)\s*=>'
        # 匹配普通函数参数
        param_pattern = r'function\s*[\u4e00-\u9fa5a-zA-Z_$]*\s*\(([^)]*)\)'
        
        identifiers = set()
        
        # 提取变量名
        for match in re.finditer(var_pattern, code):
            name = match.group(1)
            if name not in self.RESERVED_WORDS and name not in self.BUILTIN_OBJECTS and name not in self.JSON_FIELDS:
                identifiers.add(name)
        
        # 提取函数名
        for match in re.finditer(func_pattern, code):
            name = match.group(1)
            if name not in self.RESERVED_WORDS and name not in self.BUILTIN_OBJECTS and name not in self.JSON_FIELDS:
                identifiers.add(name)
        
        # 提取参数名
        for pattern in [arrow_pattern, param_pattern]:
            for match in re.finditer(pattern, code):
                params = match.group(1)
                for param in params.split(','):
                    param = param.strip()
                    # 处理默认值
                    if '=' in param:
                        param = param.split('=')[0].strip()
                    # 处理解构
                    if param.startswith('{') or param.startswith('['):
                        continue
                    if param and param not in self.RESERVED_WORDS and param not in self.BUILTIN_OBJECTS and param not in self.JSON_FIELDS:
                        identifiers.add(param)
        
        # 专门提取中文标识符（更全面的模式）
        chinese_var_pattern = r'(?:var|let|const)\s+([\u4e00-\u9fa5][\u4e00-\u9fa5a-zA-Z0-9_$]*)'
        for match in re.finditer(chinese_var_pattern, code):
            identifiers.add(match.group(1))
        
        # 提取所有看起来像中文变量的标识符（以中文开头）
        all_chinese_pattern = r'(?<![\'"\w])([\u4e00-\u9fa5][\u4e00-\u9fa5a-zA-Z0-9_$]*)(?![\'"\w])'
        for match in re.finditer(all_chinese_pattern, code):
            name = match.group(1)
            # 过滤掉注释中的中文
            if len(name) >= 2 and name not in self.RESERVED_WORDS and name not in self.JSON_FIELDS:
                identifiers.add(name)
        
        # 提取包含中文的混合标识符（如 SOCKS5白名单, TLS分片参数）
        mixed_pattern = r'\b([a-zA-Z_$][a-zA-Z0-9_$]*[\u4e00-\u9fa5][\u4e00-\u9fa5a-zA-Z0-9_$]*)\b'
        for match in re.finditer(mixed_pattern, code):
            name = match.group(1)
            if name not in self.RESERVED_WORDS and name not in self.BUILTIN_OBJECTS and name not in self.JSON_FIELDS:
                identifiers.add(name)
        
        # 提取对象属性中的中文（如 config_JSON.协议类型）
        prop_access_pattern = r'\.([a-zA-Z_$\u4e00-\u9fa5][a-zA-Z0-9_$\u4e00-\u9fa5]*)'
        for match in re.finditer(prop_access_pattern, code):
            name = match.group(1)
            # 只处理包含中文的属性名
            if re.search(r'[\u4e00-\u9fa5]', name) and name not in self.BUILTIN_OBJECTS and name not in self.JSON_FIELDS:
                identifiers.add(name)
        
        return identifiers
    
    def _obfuscate_identifiers(self, code: str) -> str:
        """混淆标识符（使用两阶段处理保护字符串）"""
        identifiers = self._extract_identifiers(code)
        
        # 为每个标识符生成混淆名
        for ident in sorted(identifiers, key=len, reverse=True):
            if ident not in self.name_map:
                self.name_map[ident] = self._generate_name()
        
        # 阶段1：提取并保护所有字符串和正则表达式
        protected = []
        result = []
        i = 0
        in_string = None
        in_regex = False
        string_start = 0
        
        while i < len(code):
            char = code[i]
            
            if in_regex:
                if char == '\\' and i + 1 < len(code):
                    i += 2
                elif char == '/':
                    i += 1
                    # 包含正则表达式标志
                    while i < len(code) and code[i] in 'gimsuy':
                        i += 1
                    # 保存正则表达式（包括标志）
                    regex_content = code[string_start:i]
                    placeholder = f"__PROTECTED_{len(protected)}__"
                    protected.append(regex_content)
                    result.append(placeholder)
                    in_regex = False
                else:
                    i += 1
                continue
            
            if in_string is not None:
                if char == '\\' and i + 1 < len(code):
                    i += 2
                elif char == in_string:
                    i += 1
                    # 保存字符串
                    string_content = code[string_start:i]
                    placeholder = f"__PROTECTED_{len(protected)}__"
                    protected.append(string_content)
                    result.append(placeholder)
                    in_string = None
                else:
                    i += 1
                continue
            
            if char in '"\'':
                in_string = char
                string_start = i
                i += 1
            elif char == '`':
                # 模板字符串需要特殊处理 - 保护静态部分，但处理 ${} 中的代码
                template_start = i
                i += 1
                while i < len(code):
                    if code[i] == '\\' and i + 1 < len(code):
                        i += 2
                    elif code[i] == '$' and i + 1 < len(code) and code[i + 1] == '{':
                        # 保存模板字符串的静态部分
                        if i > template_start:
                            static_part = code[template_start:i]
                            placeholder = f"__PROTECTED_{len(protected)}__"
                            protected.append(static_part)
                            result.append(placeholder)
                        # 添加 ${
                        result.append('${')
                        i += 2
                        # 处理表达式直到 }
                        brace_depth = 1
                        expr_start = i
                        while i < len(code) and brace_depth > 0:
                            if code[i] == '{':
                                brace_depth += 1
                            elif code[i] == '}':
                                brace_depth -= 1
                            elif code[i] == '\\' and i + 1 < len(code):
                                i += 1
                            elif code[i] in '"\'':
                                # 跳过嵌套字符串
                                quote = code[i]
                                i += 1
                                while i < len(code) and code[i] != quote:
                                    if code[i] == '\\' and i + 1 < len(code):
                                        i += 1
                                    i += 1
                            i += 1
                        # 表达式内容（不包括最后的 }）
                        expr_content = code[expr_start:i-1]
                        result.append(expr_content)
                        result.append('}')
                        template_start = i
                    elif code[i] == '`':
                        # 模板字符串结束
                        remaining = code[template_start:i+1]
                        placeholder = f"__PROTECTED_{len(protected)}__"
                        protected.append(remaining)
                        result.append(placeholder)
                        i += 1
                        break
                    else:
                        i += 1
            elif char == '/':
                # 检查是否是正则表达式
                prev_char = None
                for j in range(len(result) - 1, -1, -1):
                    c = result[j]
                    if c not in ' \t\n\r':
                        prev_char = c[-1] if c else None
                        break
                
                regex_prefix_chars = set('=([{,;:!&|?+-*/%<>^~')
                if prev_char in regex_prefix_chars or prev_char is None:
                    if i + 1 < len(code) and code[i + 1] not in '/*':
                        in_regex = True
                        string_start = i
                        i += 1
                    else:
                        result.append(char)
                        i += 1
                else:
                    result.append(char)
                    i += 1
            else:
                result.append(char)
                i += 1
        
        code_without_strings = ''.join(result)
        
        # 阶段2：替换标识符（不需要担心字符串）
        for orig, obf in sorted(self.name_map.items(), key=lambda x: len(x[0]), reverse=True):
            # 不替换对象属性，也不替换正则表达式标志位置 $/flag
            code_without_strings = re.sub(r'(?<![.\w$/])' + re.escape(orig) + r'(?!\w)', obf, code_without_strings)
        
        # 阶段3：恢复字符串
        for idx, content in enumerate(protected):
            placeholder = f"__PROTECTED_{idx}__"
            code_without_strings = code_without_strings.replace(placeholder, content)
        
        return code_without_strings
    
    def _obfuscate_strings(self, code: str) -> str:
        """混淆字符串字面量"""
        # 匹配字符串（单引号和双引号）
        string_pattern = r'(["\'])(?:(?!\1)[^\\]|\\.)*\1'
        
        def replace_string(match):
            full_str = match.group(0)
            quote = full_str[0]
            content = full_str[1:-1]
            
            # 跳过空字符串和非常短的字符串
            if len(content) < 2:
                return full_str
            
            # 跳过已经是转义序列的字符串
            if content.startswith('\\x') or content.startswith('\\u'):
                return full_str
            
            # 对敏感关键词进行加密
            sensitive_keywords = [
                'websocket', 'socket', 'proxy', 'vless', 'vmess', 'trojan',
                'shadowsocks', 'uuid', 'password', 'secret', 'token', 'auth',
                'connect', 'tunnel', 'bypass', 'vpn', 'encrypt', 'decrypt'
            ]
            
            content_lower = content.lower()
            is_sensitive = any(kw in content_lower for kw in sensitive_keywords)
            
            if is_sensitive or random.random() < 0.7:  # 70% 概率混淆
                # 使用多种编码方式
                method = random.choice(['hex', 'charcode', 'split'])
                return self._encode_string(content, method)
            
            return full_str
        
        return re.sub(string_pattern, replace_string, code)
    
    def _add_dead_code(self, code: str) -> str:
        """注入死代码（安全位置）"""
        dead_code_templates = [
            'if(false){{var _0xdead{n}=function(){{return Math.random()>2}};}}',
            'var _0xfake{n}=(function(){{return typeof window!=="undefined"?0:1}})();',
        ]
        
        # 只在安全位置插入死代码（函数体内部，不在对象字面量中）
        lines = code.split('\n')
        new_lines = []
        in_function = 0  # 跟踪函数嵌套深度
        in_object = 0    # 跟踪对象字面量深度
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 跟踪上下文
            if 'function' in stripped or '=>' in stripped:
                in_function += stripped.count('{')
            if stripped.startswith('export default {') or stripped.endswith(': {'):
                in_object += 1
            
            in_function += stripped.count('{') - stripped.count('}')
            
            new_lines.append(line)
            
            # 只在函数体内部且不在对象字面量开始处插入
            safe_position = (
                in_function > 0 and 
                in_object == 0 and
                ';' in line and 
                'export' not in stripped and
                '{' not in stripped[-5:] and  # 不在行尾的 { 后
                random.random() < 0.05  # 降低频率
            )
            
            if safe_position:
                template = random.choice(dead_code_templates)
                dead = template.format(n=random.randint(1000, 9999))
                new_lines.append(dead)
        
        return '\n'.join(new_lines)
    
    def _flatten_control_flow(self, code: str) -> str:
        """控制流扁平化（简化版）"""
        # 这是一个简化的实现，完整实现需要AST解析
        # 将简单的 if-else 转换为三元表达式
        
        # 模式: if (cond) { return x; } else { return y; }
        pattern = r'if\s*\(([^)]+)\)\s*\{\s*return\s+([^;]+);\s*\}\s*else\s*\{\s*return\s+([^;]+);\s*\}'
        
        def replace_if_else(match):
            cond = match.group(1)
            true_val = match.group(2)
            false_val = match.group(3)
            return f'return ({cond})?({true_val}):({false_val});'
        
        code = re.sub(pattern, replace_if_else, code)
        
        return code
    
    def _add_wrapper(self, code: str) -> str:
        """添加自执行函数包装（兼容 ES 模块）"""
        # 生成字符串数组解码函数
        string_array_code = ""
        if self.string_array:
            encoded_strings = [f'"{self._string_to_hex_escape(s)}"' for s in self.string_array]
            string_array_code = f"var _0xstr=[{','.join(encoded_strings)}];"
        
        # 添加反调试代码（独立的 IIFE，不包裹主代码）
        anti_debug = '''(function(){var _0xdbg=function(){try{(function(){}).constructor("debugger")();}catch(_0xe){}};setInterval(_0xdbg,1000);})();'''
        
        # 检测是否是 ES 模块（包含 import 或 export）
        has_es_module = bool(re.search(r'^\s*(import|export)\s', code, re.MULTILINE))
        
        if has_es_module:
            # ES 模块：提取 import 语句保持在顶部，不用 IIFE 包裹
            import_pattern = r'^(import\s+.*?;?\s*$)'
            imports = re.findall(import_pattern, code, re.MULTILINE)
            remaining_code = re.sub(import_pattern, '', code, flags=re.MULTILINE).strip()
            
            import_section = '\n'.join(imports)
            return f'''{import_section}
{anti_debug}
{string_array_code}
{remaining_code}'''
        else:
            # 普通脚本：使用 IIFE 包裹
            return f'''(function(){{
{anti_debug}
{string_array_code}
{code}
}})();'''
    
    def _remove_comments(self, code: str) -> str:
        """移除所有注释（保护字符串和正则表达式中的内容）"""
        result = []
        i = 0
        in_string = None
        in_regex = False
        template_depth = 0  # 模板字符串 ${} 嵌套深度
        regex_prefix_chars = set('=([{,;:!&|?+-*/%<>^~')
        
        while i < len(code):
            char = code[i]
            
            # 在正则表达式中
            if in_regex:
                result.append(char)
                if char == '\\' and i + 1 < len(code):
                    result.append(code[i + 1])
                    i += 2
                elif char == '/':
                    in_regex = False
                    i += 1
                    while i < len(code) and code[i] in 'gimsuy':
                        result.append(code[i])
                        i += 1
                else:
                    i += 1
                continue
            
            # 在字符串中（包括模板字符串）
            if in_string is not None:
                result.append(char)
                if char == '\\' and i + 1 < len(code):
                    result.append(code[i + 1])
                    i += 2
                elif in_string == '`' and char == '$' and i + 1 < len(code) and code[i + 1] == '{':
                    # 模板字符串中的 ${
                    result.append(code[i + 1])
                    template_depth += 1
                    i += 2
                elif in_string == '`' and template_depth > 0 and char == '}':
                    # 模板字符串中的 } 结束表达式
                    template_depth -= 1
                    i += 1
                elif char == in_string and template_depth == 0:
                    in_string = None
                    i += 1
                else:
                    i += 1
                continue
            
            # 普通代码
            if char in '"\'`':
                in_string = char
                result.append(char)
                i += 1
            elif char == '/' and i + 1 < len(code):
                next_char = code[i + 1]
                
                # 检查前一个非空白字符
                prev_char = None
                for j in range(len(result) - 1, -1, -1):
                    if result[j] not in ' \t\n\r':
                        prev_char = result[j]
                        break
                
                is_regex_context = prev_char in regex_prefix_chars or prev_char is None
                
                if next_char == '/':
                    # 单行注释 - 跳到行尾
                    while i < len(code) and code[i] != '\n':
                        i += 1
                elif next_char == '*':
                    # 多行注释
                    i += 2
                    while i + 1 < len(code) and not (code[i] == '*' and code[i + 1] == '/'):
                        i += 1
                    i += 2
                elif is_regex_context:
                    # 正则表达式开始
                    in_regex = True
                    result.append(char)
                    i += 1
                else:
                    # 除法运算符
                    result.append(char)
                    i += 1
            else:
                result.append(char)
                i += 1
        
        return ''.join(result)
    
    def _obfuscate_all_strings(self, code: str) -> str:
        """强制加密所有字符串（包括中文和模板字符串）"""
        # 首先处理普通字符串（包括复杂字符串）
        # 使用更宽松的模式匹配所有字符串
        
        def replace_single_quoted(match):
            full_str = match.group(0)
            content = full_str[1:-1]
            if not content:
                return full_str
            # 已经是转义的跳过
            if content.startswith('\\x') or content.startswith('\\u'):
                return full_str
            # 中文字符串必须加密
            has_chinese = bool(re.search(r'[\u4e00-\u9fa5]', content))
            if has_chinese:
                return self._string_to_charcode_array(content)
            method = random.choice(['hex', 'charcode', 'split'])
            return self._encode_string(content, method)
        
        def replace_double_quoted(match):
            full_str = match.group(0)
            content = full_str[1:-1]
            if not content:
                return full_str
            if content.startswith('\\x') or content.startswith('\\u'):
                return full_str
            has_chinese = bool(re.search(r'[\u4e00-\u9fa5]', content))
            if has_chinese:
                return self._string_to_charcode_array(content)
            method = random.choice(['hex', 'charcode', 'split'])
            return self._encode_string(content, method)
        
        # 分别处理单引号和双引号字符串
        code = re.sub(r"'(?:[^'\\]|\\.)*'", replace_single_quoted, code)
        code = re.sub(r'"(?:[^"\\]|\\.)*"', replace_double_quoted, code)
        
        # 处理模板字符串中的中文（简化处理：只替换静态模板字符串）
        # 匹配不含 ${} 的简单模板字符串
        template_pattern = r'`([^`$]*)`'
        
        def replace_template(match):
            content = match.group(1)
            if not content:
                return match.group(0)
            
            # 检查是否包含中文
            has_chinese = bool(re.search(r'[\u4e00-\u9fa5]', content))
            if has_chinese:
                return self._string_to_charcode_array(content)
            return match.group(0)
        
        code = re.sub(template_pattern, replace_template, code)
        
        # 处理对象属性名中的中文
        # 匹配 { 中文: ... } 或 obj.中文
        prop_pattern = r'(?<=[{,\s])(["\']?)([\u4e00-\u9fa5][\u4e00-\u9fa5a-zA-Z0-9_$]*)(\1)\s*:'
        
        def replace_prop(match):
            quote = match.group(1)
            name = match.group(2)
            # 将中文属性名转换为计算属性
            encoded = self._string_to_charcode_array(name)
            return f'[{encoded}]:'
        
        code = re.sub(prop_pattern, replace_prop, code)
        
        return code

    def obfuscate(self, code: str, 
                  obfuscate_identifiers: bool = True,
                  obfuscate_strings: bool = True,
                  add_dead_code: bool = True,
                  flatten_control_flow: bool = True,
                  add_wrapper: bool = True,
                  add_anti_debug: bool = True,
                  remove_comments: bool = True,
                  aggressive_strings: bool = True) -> str:
        """
        执行完整的代码混淆
        
        Args:
            code: 要混淆的 JavaScript 代码
            obfuscate_identifiers: 是否混淆变量名/函数名
            obfuscate_strings: 是否加密字符串
            add_dead_code: 是否注入死代码
            flatten_control_flow: 是否扁平化控制流
            add_wrapper: 是否添加包装函数
            add_anti_debug: 是否添加反调试代码
            remove_comments: 是否移除注释
            aggressive_strings: 是否强制加密所有字符串
        
        Returns:
            混淆后的代码
        """
        result = code
        
        # 首先移除注释
        if remove_comments:
            result = self._remove_comments(result)
        
        if flatten_control_flow:
            result = self._flatten_control_flow(result)
        
        if obfuscate_strings:
            if aggressive_strings:
                result = self._obfuscate_all_strings(result)
            else:
                result = self._obfuscate_strings(result)
        
        if obfuscate_identifiers:
            result = self._obfuscate_identifiers(result)
        
        if add_dead_code:
            result = self._add_dead_code(result)
        
        if add_wrapper:
            result = self._add_wrapper(result)
        elif add_anti_debug:
            # 单独添加反调试
            anti_debug = '(function(){setInterval(function(){try{(function(){}).constructor("debugger")();}catch(e){}},1000);})();'
            result = anti_debug + result
        
        # 移除多余空白
        result = re.sub(r'\n\s*\n', '\n', result)
        
        return result


def obfuscate_js(code: str, level: str = 'high', seed: str = None) -> str:
    """
    混淆 JavaScript 代码
    
    Args:
        code: JavaScript 代码
        level: 混淆级别 ('low', 'medium', 'high', 'maximum')
        seed: 随机种子（用于可重现的混淆）
    
    Returns:
        混淆后的代码
    """
    obfuscator = JSObfuscator(seed=seed)
    
    if level == 'low':
        return obfuscator.obfuscate(
            code,
            obfuscate_identifiers=True,
            obfuscate_strings=False,
            add_dead_code=False,
            flatten_control_flow=False,
            add_wrapper=False,
            add_anti_debug=False,
            remove_comments=True,
            aggressive_strings=False
        )
    elif level == 'medium':
        return obfuscator.obfuscate(
            code,
            obfuscate_identifiers=True,
            obfuscate_strings=True,
            add_dead_code=False,
            flatten_control_flow=False,
            add_wrapper=True,
            add_anti_debug=False,
            remove_comments=True,
            aggressive_strings=False
        )
    elif level == 'high':
        return obfuscator.obfuscate(
            code,
            obfuscate_identifiers=True,
            obfuscate_strings=True,
            add_dead_code=True,
            flatten_control_flow=True,
            add_wrapper=True,
            add_anti_debug=True,
            remove_comments=True,
            aggressive_strings=True
        )
    else:  # maximum
        return obfuscator.obfuscate(
            code,
            obfuscate_identifiers=True,
            obfuscate_strings=True,
            add_dead_code=True,
            flatten_control_flow=True,
            add_wrapper=True,
            add_anti_debug=True,
            remove_comments=True,
            aggressive_strings=True
        )


def obfuscate_html_js(html: str, level: str = 'high', seed: str = None) -> str:
    """
    混淆 HTML 中的所有 JavaScript 代码
    
    Args:
        html: HTML 代码
        level: 混淆级别
        seed: 随机种子
    
    Returns:
        混淆后的 HTML
    """
    script_pattern = r'(<script[^>]*>)(.*?)(</script>)'
    
    def replace_script(match):
        open_tag = match.group(1)
        content = match.group(2)
        close_tag = match.group(3)
        
        # 跳过外部脚本
        if 'src=' in open_tag:
            return match.group(0)
        
        # 跳过空脚本
        if not content.strip():
            return match.group(0)
        
        try:
            obfuscated = obfuscate_js(content, level=level, seed=seed)
            return f"{open_tag}{obfuscated}{close_tag}"
        except Exception:
            return match.group(0)
    
    return re.sub(script_pattern, replace_script, html, flags=re.DOTALL | re.IGNORECASE)

