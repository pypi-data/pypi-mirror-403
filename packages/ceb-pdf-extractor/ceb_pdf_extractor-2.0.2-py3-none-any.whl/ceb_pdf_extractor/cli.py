"""命令行界面"""

import argparse
import os
import sys

# 从各个模块导入提取器类
from .account_query import PDFTableExtractor_AccountQuery
from .account_query_other import PDFTableExtractor_AccountQuery_other
from .personal import PDFTableExtractor_Personal
from .company import PDFTableExtractor_Company
from .nowatermark import PDFTableExtractor_NoWatermark

def detect_pdf_type(pdf_path):
    """检测PDF类型"""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        first_page_text = doc[0].get_text("text")
        doc.close()

        # 检测逻辑
        if "交易对方名" in first_page_text and "借贷" in first_page_text:
            # 可以进一步区分是哪种账户查询版
            return "account_query_other"
        elif "借贷" in first_page_text:
            return "account_query"
        elif "客户姓名" in first_page_text and ("个人版" in first_page_text or "对账单" in first_page_text):
            return "personal"
        elif "账户名称" in first_page_text and "公司版" in first_page_text:
            return "company"
        elif "账户名称" in first_page_text and "查询起止日期" in first_page_text:
            return "nowatermark"
        else:
            # 尝试更多检测
            if "光大银行" in first_page_text:
                if "交易明细" in first_page_text:
                    return "account_query"
                elif "对账单" in first_page_text:
                    return "personal"
    except Exception:
        pass
    return "unknown"

def create_extractor(pdf_path, extractor_type="auto", **kwargs):
    """
    根据PDF类型创建提取器

    参数:
        pdf_path: PDF文件路径
        extractor_type: 提取器类型，可选 "auto", "account_query", "account_query_other",
                       "personal", "company", "nowatermark"
        **kwargs: 传递给提取器的参数

    返回:
        提取器实例
    """
    if extractor_type == "auto":
        extractor_type = detect_pdf_type(pdf_path)

    if extractor_type == "account_query":
        return PDFTableExtractor_AccountQuery(pdf_path, **kwargs)
    elif extractor_type == "account_query_other":
        return PDFTableExtractor_AccountQuery_other(pdf_path, **kwargs)
    elif extractor_type == "personal":
        return PDFTableExtractor_Personal(pdf_path, **kwargs)
    elif extractor_type == "company":
        return PDFTableExtractor_Company(pdf_path, **kwargs)
    elif extractor_type == "nowatermark":
        return PDFTableExtractor_NoWatermark(pdf_path, **kwargs)
    else:
        raise ValueError(f"无法识别的提取器类型: {extractor_type}")

# 各个提取器的命令行入口函数（保持原样）
def account_query_main():
    """账户交易明细查询版（从借贷开始）命令行入口"""
    parser = argparse.ArgumentParser(description='光大银行账户交易明细查询PDF提取工具（从借贷开始）')
    parser.add_argument('-f', '--file', help='PDF文件路径')
    parser.add_argument('-d', '--directory', help='包含PDF文件的文件夹路径')
    parser.add_argument('-m', '--mode', choices=['multiple', 'single'],
                       default='multiple', help='输出模式: multiple(多个文件) 或 single(单个总文件)')
    parser.add_argument('-o', '--output', help='输出目录（可选）')

    args = parser.parse_args()

    if not args.file and not args.directory:
        parser.print_help()
        return

    # 处理单个文件
    if args.file:
        if not os.path.exists(args.file):
            print(f"❌ 文件不存在: {args.file}")
            return

        extractor = PDFTableExtractor_AccountQuery(args.file, output_mode=args.mode)
        if args.output:
            extractor.output_dir = args.output
        result = extractor.process()

        if result and not isinstance(result, dict):
            print(f"\n✅ 处理完成！")

    # 处理文件夹
    elif args.directory:
        if not os.path.exists(args.directory):
            print(f"❌ 文件夹不存在: {args.directory}")
            return

        pdf_files = []
        for root, dirs, files in os.walk(args.directory):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))

        if not pdf_files:
            print(f"⚠️  在文件夹 {args.directory} 中未找到PDF文件")
            return

        success_count = 0
        fail_count = 0

        for pdf_file in pdf_files:
            try:
                extractor = PDFTableExtractor_AccountQuery(pdf_file, output_mode=args.mode)
                if args.output:
                    extractor.output_dir = args.output
                result = extractor.process()

                if result and not isinstance(result, dict):
                    success_count += 1
                    print(f"✅ 处理成功: {os.path.basename(pdf_file)}")
                else:
                    fail_count += 1
                    print(f"❌ 处理失败: {os.path.basename(pdf_file)}")
            except Exception as e:
                fail_count += 1
                print(f"❌ 处理异常: {os.path.basename(pdf_file)} - {str(e)}")

        print(f"\n📋 批处理完成！")
        print(f"✅ 处理成功: {success_count} 个文件")
        print(f"❌ 处理失败: {fail_count} 个文件")

def account_query_other_main():
    """账户交易明细查询版（从交易对方名开始）命令行入口"""
    parser = argparse.ArgumentParser(description='光大银行账户交易明细查询PDF提取工具（从交易对方名开始）')
    parser.add_argument('-f', '--file', help='PDF文件路径')
    parser.add_argument('-d', '--directory', help='包含PDF文件的文件夹路径')
    parser.add_argument('-m', '--mode', choices=['separate', 'single'],
                       default='separate', help='输出模式: separate(多个文件) 或 single(单个总文件)')
    parser.add_argument('-o', '--output', help='输出目录（可选）')

    args = parser.parse_args()

    if not args.file and not args.directory:
        parser.print_help()
        return

    # 处理单个文件
    if args.file:
        if not os.path.exists(args.file):
            print(f"❌ 文件不存在: {args.file}")
            return

        extractor = PDFTableExtractor_AccountQuery_other(args.file)
        if args.output:
            extractor.output_dir = args.output
        result = extractor.process(mode=args.mode)

        if result and not isinstance(result, dict):
            print(f"\n✅ 处理完成！")

    # 处理文件夹
    elif args.directory:
        if not os.path.exists(args.directory):
            print(f"❌ 文件夹不存在: {args.directory}")
            return

        pdf_files = []
        for root, dirs, files in os.walk(args.directory):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))

        if not pdf_files:
            print(f"⚠️  在文件夹 {args.directory} 中未找到PDF文件")
            return

        success_count = 0
        fail_count = 0

        for pdf_file in pdf_files:
            try:
                extractor = PDFTableExtractor_AccountQuery_other(pdf_file)
                if args.output:
                    extractor.output_dir = args.output
                result = extractor.process(mode=args.mode)

                if result and not isinstance(result, dict):
                    success_count += 1
                    print(f"✅ 处理成功: {os.path.basename(pdf_file)}")
                else:
                    fail_count += 1
                    print(f"❌ 处理失败: {os.path.basename(pdf_file)}")
            except Exception as e:
                fail_count += 1
                print(f"❌ 处理异常: {os.path.basename(pdf_file)} - {str(e)}")

        print(f"\n📋 批处理完成！")
        print(f"✅ 处理成功: {success_count} 个文件")
        print(f"❌ 处理失败: {fail_count} 个文件")

def personal_main():
    """个人版命令行入口"""
    parser = argparse.ArgumentParser(description='光大银行个人版PDF对账单提取工具')
    parser.add_argument('-f', '--file', help='PDF文件路径', required=True)
    parser.add_argument('-t', '--type', choices=['split', 'merged'],
                       default='split', help='导出类型: split(分表) 或 merged(总表)')
    parser.add_argument('-o', '--output', help='输出目录（可选）')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
        return

    extractor = PDFTableExtractor_Personal(args.file, export_type=args.type)
    if args.output:
        extractor.output_dir = args.output

    result = extractor.process()

    if isinstance(result, list) and len(result) > 0:
        print(f"\n✅ 处理完成！")
        print(f"📁 输出目录: {extractor.output_dir}")

def company_main():
    """公司版命令行入口"""
    parser = argparse.ArgumentParser(description='光大银行公司版PDF对账单提取工具')
    parser.add_argument('-f', '--file', help='PDF文件路径', required=True)
    parser.add_argument('-t', '--type', choices=['split', 'merged'],
                       default='split', help='导出类型: split(分表) 或 merged(总表)')
    parser.add_argument('-o', '--output', help='输出目录（可选）')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
        return

    extractor = PDFTableExtractor_Company(args.file, export_type=args.type)
    if args.output:
        extractor.output_dir = args.output

    result = extractor.process()

    if isinstance(result, list) and len(result) > 0:
        print(f"\n✅ 处理完成！")
        print(f"📁 输出目录: {extractor.output_dir}")

def nowatermark_main():
    """无水印版命令行入口"""
    parser = argparse.ArgumentParser(description='光大银行无水印版PDF对账单提取工具')
    parser.add_argument('-f', '--file', help='PDF文件路径', required=True)
    parser.add_argument('-t', '--type', choices=['split', 'merged'],
                       default='split', help='导出类型: split(分表) 或 merged(总表)')
    parser.add_argument('-o', '--output', help='输出目录（可选）')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
        return

    extractor = PDFTableExtractor_NoWatermark(args.file, export_type=args.type)
    if args.output:
        extractor.output_dir = args.output

    result = extractor.process()

    if isinstance(result, list) and len(result) > 0:
        print(f"\n✅ 处理完成！")
        print(f"📁 输出目录: {extractor.output_dir}")

def main():
    """统一命令行入口（自动检测PDF类型）"""
    parser = argparse.ArgumentParser(description='光大银行PDF对账单提取工具')
    parser.add_argument('-f', '--file', help='PDF文件路径', required=True)
    parser.add_argument('--extractor-type', choices=['auto', 'account_query', 'account_query_other',
                                                     'personal', 'company', 'nowatermark'],
                       default='auto', help='指定提取器类型（默认自动检测）')
    parser.add_argument('--account-mode', choices=['multiple', 'single', 'separate'],
                       help='账户查询版输出模式')
    parser.add_argument('--export-type', choices=['split', 'merged'],
                       help='个人版/公司版/无水印版导出类型')
    parser.add_argument('-o', '--output', help='输出目录（可选）')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
        return

    # 检测PDF类型
    if args.extractor_type == "auto":
        extractor_type = detect_pdf_type(args.file)
        print(f"📄 检测到PDF类型: {extractor_type}")
    else:
        extractor_type = args.extractor_type
        print(f"📄 使用指定提取器类型: {extractor_type}")

    # 创建提取器
    if extractor_type == "account_query":
        mode = args.account_mode if args.account_mode else "multiple"
        extractor = PDFTableExtractor_AccountQuery(args.file, output_mode=mode)
    elif extractor_type == "account_query_other":
        mode = args.account_mode if args.account_mode else "separate"
        extractor = PDFTableExtractor_AccountQuery_other(args.file)
    elif extractor_type == "personal":
        export_type = args.export_type if args.export_type else "split"
        extractor = PDFTableExtractor_Personal(args.file, export_type=export_type)
    elif extractor_type == "company":
        export_type = args.export_type if args.export_type else "split"
        extractor = PDFTableExtractor_Company(args.file, export_type=export_type)
    elif extractor_type == "nowatermark":
        export_type = args.export_type if args.export_type else "split"
        extractor = PDFTableExtractor_NoWatermark(args.file, export_type=export_type)
    else:
        print("❌ 无法识别PDF类型，请使用 --extractor-type 参数指定")
        return

    if args.output:
        extractor.output_dir = args.output

    result = extractor.process()

    if result and (isinstance(result, list) or not isinstance(result, dict)):
        print(f"\n✅ 处理完成！")
        print(f"📁 输出目录: {extractor.output_dir}")

# 批量处理函数
def process_multiple_files(file_paths, extractor_type="auto", **kwargs):
    """
    批量处理多个PDF文件
    """
    results = []

    for i, file_path in enumerate(file_paths, 1):
        print(f"处理文件 {i}/{len(file_paths)}: {file_path}")

        try:
            extractor = create_extractor(file_path, extractor_type, **kwargs)
            result = extractor.process()
            results.append({
                "file": file_path,
                "success": True,
                "result": result
            })
            print(f"  ✅ 处理成功")

        except Exception as e:
            results.append({
                "file": file_path,
                "success": False,
                "error": str(e)
            })
            print(f"  ❌ 处理失败: {str(e)}")

    return results

if __name__ == "__main__":
    main()