"""
X27CN 命令行工具

用法:
    x27cn encrypt <file> [output] [--key=密钥]
    x27cn decrypt <file> [output] [--key=密钥]
    x27cn obfuscate <file> [output] [--key=密钥]
    x27cn protect <file> [output] [--level=high]  # 高级混淆
"""

import argparse
import sys
from .core import encrypt, decrypt, DEFAULT_KEY
from .obfuscate import obfuscate_file
from .advanced import obfuscate_js, obfuscate_html_js


def main():
    parser = argparse.ArgumentParser(
        prog='x27cn',
        description='X27CN 代码混淆加密工具'
    )
    parser.add_argument('--version', action='version', version='x27cn 1.2.0')
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # encrypt 命令
    enc_parser = subparsers.add_parser('encrypt', help='加密文本或文件')
    enc_parser.add_argument('input', help='输入文件或文本')
    enc_parser.add_argument('output', nargs='?', help='输出文件（可选）')
    enc_parser.add_argument('--key', '-k', default=DEFAULT_KEY, help='加密密钥')
    enc_parser.add_argument('--text', '-t', action='store_true', help='将 input 作为文本而非文件')
    
    # decrypt 命令
    dec_parser = subparsers.add_parser('decrypt', help='解密文本或文件')
    dec_parser.add_argument('input', help='输入文件或加密文本')
    dec_parser.add_argument('output', nargs='?', help='输出文件（可选）')
    dec_parser.add_argument('--key', '-k', default=DEFAULT_KEY, help='解密密钥')
    dec_parser.add_argument('--text', '-t', action='store_true', help='将 input 作为文本而非文件')
    
    # obfuscate 命令
    obf_parser = subparsers.add_parser('obfuscate', help='混淆加密文件（生成自解密代码）')
    obf_parser.add_argument('input', help='输入文件 (.html/.js/.css)')
    obf_parser.add_argument('output', nargs='?', help='输出文件（可选）')
    obf_parser.add_argument('--key', '-k', default=DEFAULT_KEY, help='加密密钥')
    
    # protect 命令 - 高级混淆
    prot_parser = subparsers.add_parser('protect', help='高级代码混淆（变量名/字符串/控制流）')
    prot_parser.add_argument('input', help='输入文件 (.js/.html)')
    prot_parser.add_argument('output', nargs='?', help='输出文件（可选）')
    prot_parser.add_argument('--level', '-l', choices=['low', 'medium', 'high', 'maximum'], 
                            default='high', help='混淆级别 (low/medium/high/maximum)')
    prot_parser.add_argument('--seed', '-s', default=None, help='随机种子（用于可重现的混淆）')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    try:
        if args.command == 'encrypt':
            if args.text:
                result = encrypt(args.input, args.key)
                print(result)
            else:
                with open(args.input, 'r', encoding='utf-8') as f:
                    content = f.read()
                result = encrypt(content, args.key)
                if args.output:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(result)
                    print(f'加密完成: {args.output}')
                else:
                    print(result)
        
        elif args.command == 'decrypt':
            if args.text:
                result = decrypt(args.input, args.key)
                print(result)
            else:
                with open(args.input, 'r', encoding='utf-8') as f:
                    content = f.read()
                result = decrypt(content, args.key)
                if args.output:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(result)
                    print(f'解密完成: {args.output}')
                else:
                    print(result)
        
        elif args.command == 'obfuscate':
            output = obfuscate_file(args.input, args.output, args.key)
            print(f'混淆完成: {output}')
        
        elif args.command == 'protect':
            with open(args.input, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 根据文件类型选择混淆方法
            if args.input.lower().endswith('.js'):
                result = obfuscate_js(content, level=args.level, seed=args.seed)
            elif args.input.lower().endswith('.html') or args.input.lower().endswith('.htm'):
                result = obfuscate_html_js(content, level=args.level, seed=args.seed)
            else:
                print(f'错误: 不支持的文件类型，仅支持 .js/.html', file=sys.stderr)
                sys.exit(1)
            
            output_path = args.output
            if not output_path:
                import os
                base, ext = os.path.splitext(args.input)
                output_path = f'{base}.protected{ext}'
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f'高级混淆完成: {output_path}')
            print(f'混淆级别: {args.level}')
    
    except FileNotFoundError:
        print(f'错误: 文件不存在 - {args.input}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'错误: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

