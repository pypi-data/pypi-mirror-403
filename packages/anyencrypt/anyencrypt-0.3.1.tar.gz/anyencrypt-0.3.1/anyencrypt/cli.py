"""
命令行接口模块
提供 anyencrypt 命令行工具
"""

import sys
import click
from pathlib import Path
from getpass import getpass

from . import __version__
from .crypto import encrypt_text, decrypt_text, encrypt_file, decrypt_file
from .i18n import setup_i18n

_ = setup_i18n()

DOC_MAIN = _(
    "AnyEncrypt - 简单易用的加密解密命令行工具\n\n"
    "支持文本和文件的加密解密操作。"
)
DOC_ENCRYPT = _(
    "加密文本或文件\n\n"
    "示例：\n"
    "\b\n"
    "    # 加密文本\n"
    "    anyencrypt encrypt -t \"Hello World\"\n\n"
    "    # 加密文件\n"
    "    anyencrypt encrypt -f input.txt -o encrypted.bin"
)
DOC_DECRYPT = _(
    "解密文本或文件\n\n"
    "示例：\n"
    "\b\n"
    "    # 解密文本\n"
    "    anyencrypt decrypt -t \"gAAAAAB...\"\n\n"
    "    # 解密文件\n"
    "    anyencrypt decrypt -f encrypted.bin -o decrypted.txt"
)
DOC_INTERACTIVE = _("交互式模式 - 引导用户完成加密/解密操作")


@click.group(invoke_without_command=True, help=DOC_MAIN)
@click.version_option(version=__version__, prog_name="anyencrypt")
@click.pass_context
def main(ctx):
    """
    AnyEncrypt - 简单易用的加密解密命令行工具
    
    支持文本和文件的加密解密操作。
    """
    # 如果没有子命令，进入交互式模式
    if ctx.invoked_subcommand is None:
        interactive_mode()


@main.command(help=DOC_ENCRYPT)
@click.option("-t", "--text", help=_("要加密的文本"))
@click.option(
    "-f", "--file", type=click.Path(exists=True), help=_("要加密的文件路径")
)
@click.option("-o", "--output", type=click.Path(), help=_("输出文件路径（文件加密时使用）"))
@click.option(
    "-p", "--password", help=_("加密密码（不建议使用，会在命令历史中留下记录）")
)
def encrypt(text, file, output, password):
    """
    加密文本或文件
    
    示例：
    \b
        # 加密文本
        anyencrypt encrypt -t "Hello World"
        
        # 加密文件
        anyencrypt encrypt -f input.txt -o encrypted.bin
    """
    # 获取密码
    if not password:
        password = getpass(_("请输入加密密码: "))
        confirm_password = getpass(_("请再次输入密码: "))
        if password != confirm_password:
            click.echo(_("错误: 两次输入的密码不一致"), err=True)
            sys.exit(1)
    
    if not password:
        click.echo(_("错误: 密码不能为空"), err=True)
        sys.exit(1)
    
    try:
        if text:
            # 加密文本
            encrypted = encrypt_text(text, password)
            click.echo(_("\n加密结果:"))
            click.echo(encrypted)
            
        elif file:
            # 加密文件
            if not output:
                output = str(Path(file).with_suffix('.encrypted'))
            
            encrypt_file(file, output, password)
            click.echo(_("✓ 文件加密成功: {output}").format(output=output))
            
        else:
            click.echo(_("错误: 请指定要加密的文本 (-t) 或文件 (-f)"), err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(_("错误: {error}").format(error=str(e)), err=True)
        sys.exit(1)


@main.command(help=DOC_DECRYPT)
@click.option("-t", "--text", help=_("要解密的文本"))
@click.option(
    "-f", "--file", type=click.Path(exists=True), help=_("要解密的文件路径")
)
@click.option("-o", "--output", type=click.Path(), help=_("输出文件路径（文件解密时使用）"))
@click.option(
    "-p", "--password", help=_("解密密码（不建议使用，会在命令历史中留下记录）")
)
def decrypt(text, file, output, password):
    """
    解密文本或文件
    
    示例：
    \b
        # 解密文本
        anyencrypt decrypt -t "gAAAAAB..."
        
        # 解密文件
        anyencrypt decrypt -f encrypted.bin -o decrypted.txt
    """
    # 获取密码
    if not password:
        password = getpass(_("请输入解密密码: "))
    
    if not password:
        click.echo(_("错误: 密码不能为空"), err=True)
        sys.exit(1)
    
    try:
        if text:
            # 解密文本
            decrypted = decrypt_text(text, password)
            click.echo(_("\n解密结果:"))
            click.echo(decrypted)
            
        elif file:
            # 解密文件
            if not output:
                # 尝试去掉 .encrypted 后缀
                file_path = Path(file)
                if file_path.suffix == '.encrypted':
                    output = str(file_path.with_suffix(''))
                else:
                    output = str(file_path.with_suffix('.decrypted'))
            
            decrypt_file(file, output, password)
            click.echo(_("✓ 文件解密成功: {output}").format(output=output))
            
        else:
            click.echo(_("错误: 请指定要解密的文本 (-t) 或文件 (-f)"), err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(_("错误: {error}").format(error=str(e)), err=True)
        sys.exit(1)


def interactive_mode():
    """
    交互式模式 - 引导用户完成加密/解密操作
    """
    click.echo("=" * 50)
    click.echo(_("  AnyEncrypt - 加密解密工具"))
    click.echo("=" * 50)
    click.echo()
    
    # 步骤1: 选择操作类型
    click.echo(_("请选择操作类型:"))
    click.echo(_("  [1] 加密"))
    click.echo(_("  [2] 解密"))
    choice = click.prompt(_("请输入选项"), type=int, default=1)
    
    if choice not in [1, 2]:
        click.echo(_("错误: 无效的选项"), err=True)
        sys.exit(1)
    
    is_encrypt = choice == 1
    operation = _("加密") if is_encrypt else _("解密")
    click.echo()
    
    # 步骤2: 选择处理类型（文本或文件）
    click.echo(_("请选择处理类型:"))
    click.echo(_("  [1] 文本"))
    click.echo(_("  [2] 文件"))
    type_choice = click.prompt(_("请输入选项"), type=int, default=1)
    
    if type_choice not in [1, 2]:
        click.echo(_("错误: 无效的选项"), err=True)
        sys.exit(1)
    
    is_text = type_choice == 1
    click.echo()
    
    # 步骤3: 获取密码
    if is_encrypt:
        password = getpass(_("请输入{operation}密码: ").format(operation=operation))
        confirm_password = getpass(_("请再次输入密码: "))
        if password != confirm_password:
            click.echo(_("错误: 两次输入的密码不一致"), err=True)
            sys.exit(1)
    else:
        password = getpass(_("请输入{operation}密码: ").format(operation=operation))
    
    if not password:
        click.echo(_("错误: 密码不能为空"), err=True)
        sys.exit(1)
    
    click.echo()
    
    # 步骤4: 获取输入内容并执行操作
    try:
        if is_text:
            # 处理文本
            if is_encrypt:
                plaintext = click.prompt(_("请输入要加密的文本"))
                encrypted = encrypt_text(plaintext, password)
                click.echo()
                click.echo("=" * 50)
                click.echo(_("✓ 加密成功!"))
                click.echo("=" * 50)
                click.echo()
                click.echo(_("加密结果:"))
                click.echo(encrypted)
            else:
                ciphertext = click.prompt(_("请输入要解密的密文"))
                decrypted = decrypt_text(ciphertext, password)
                click.echo()
                click.echo("=" * 50)
                click.echo(_("✓ 解密成功!"))
                click.echo("=" * 50)
                click.echo()
                click.echo(_("解密结果:"))
                click.echo(decrypted)
        else:
            # 处理文件
            if is_encrypt:
                input_file = click.prompt(_("请输入要加密的文件路径"))
                input_path = Path(input_file)
                if not input_path.exists():
                    click.echo(
                        _("错误: 文件不存在: {path}").format(path=input_file),
                        err=True,
                    )
                    sys.exit(1)
                
                default_output = str(input_path.with_suffix('.encrypted'))
                output_file = click.prompt(_("请输入输出文件路径"), default=default_output)
                
                encrypt_file(input_file, output_file, password)
                click.echo()
                click.echo("=" * 50)
                click.echo(_("✓ 文件加密成功: {path}").format(path=output_file))
                click.echo("=" * 50)
            else:
                input_file = click.prompt(_("请输入要解密的文件路径"))
                input_path = Path(input_file)
                if not input_path.exists():
                    click.echo(
                        _("错误: 文件不存在: {path}").format(path=input_file),
                        err=True,
                    )
                    sys.exit(1)
                
                # 智能默认输出文件名
                if input_path.suffix == '.encrypted':
                    default_output = str(input_path.with_suffix(''))
                else:
                    default_output = str(input_path.with_suffix('.decrypted'))
                output_file = click.prompt(_("请输入输出文件路径"), default=default_output)
                
                decrypt_file(input_file, output_file, password)
                click.echo()
                click.echo("=" * 50)
                click.echo(_("✓ 文件解密成功: {path}").format(path=output_file))
                click.echo("=" * 50)
                
    except Exception as e:
        click.echo()
        click.echo("=" * 50)
        click.echo(_("错误: {error}").format(error=str(e)), err=True)
        click.echo("=" * 50)
        sys.exit(1)


if __name__ == '__main__':
    main()


main.__doc__ = DOC_MAIN
encrypt.__doc__ = DOC_ENCRYPT
decrypt.__doc__ = DOC_DECRYPT
interactive_mode.__doc__ = DOC_INTERACTIVE
