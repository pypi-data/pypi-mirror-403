import re


class BibTeXManager:
    """BibTeX文件管理器,用于提取和插入BibTeX条目"""
    
    # 类属性：用于存储每个会话的 BibTeXManager 实例
    _shared_managers = {}

    def __init__(self):
        """
        这是类的**实例变量**（属性），用来存储数据:

```python
self.bib_list = []      # 存储所有完整的bib条目字符串
self.cite_keys = []     # 存储所有bib的cite key（引用键）
```

**举例说明:**

当你调用 `manager.extract_bib_entries("references.txt")` 后：

**`self.bib_list`** 会存储类似这样的列表:
```python
[
    "@article{smith2020,\n  title={Machine Learning},\n  author={Smith, J.},\n  year={2020}\n}",
    "@book{jones2021,\n  title={Deep Learning},\n  author={Jones, A.},\n  year={2021}\n}",
    "@inproceedings{wang2022,\n  title={AI Systems},\n  author={Wang, L.},\n  year={2022}\n}"
]
```

**`self.cite_keys`** 会存储:
```python
["smith2020", "jones2021", "wang2022"]
```

**为什么要用 `self.`?**
- `self.` 表示这些变量属于**这个类的实例**
- 这样在类的任何方法中都可以访问这些数据
- 比如你可以用 `manager.bib_list` 直接访问所有bib条目

简单说：`self.bib_list` 就是这个管理器记住的所有bib条目！

        """
        self.bib_list = []
        self.cite_keys = []

    def extract_bib_entries(self, filename):
        """
        从txt文件中提取所有BibTeX条目并存储为列表（去重，保留首次出现）

        参数:
            filename: txt文件路径

        返回:
            bib_list: 包含所有去重后完整bib条目字符串的列表
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()

            # 匹配完整的BibTeX条目
            pattern = r'@\w+\s*\{[^@]*?\n\}'
            matches = re.findall(pattern, content, re.DOTALL)

            # 去重逻辑：按cite key去重，保留首次出现的条目
            unique_cite_keys = set()  # 记录已出现的cite key
            unique_bib_list = []  # 存储去重后的条目

            for match in matches:
                bib = match.strip()
                # 提取当前条目的cite key
                cite_key_match = re.search(r'@\w+\s*\{\s*([^,\s]+)', bib)
                if cite_key_match:
                    cite_key = cite_key_match.group(1)
                    # 仅当cite key未出现过时，才保留条目
                    if cite_key not in unique_cite_keys:
                        unique_cite_keys.add(cite_key)
                        unique_bib_list.append(bib)

            # 更新实例变量（去重后）
            self.bib_list = unique_bib_list
            self.cite_keys = list(unique_cite_keys)  # 同步去重后的cite key

            print(f"✓ 原始提取 {len(matches)} 个BibTeX条目，去重后剩余 {len(self.bib_list)} 个")
            return self.bib_list

        except FileNotFoundError:
            print(f"错误: 找不到文件 '{filename}'")
            return []
        except Exception as e:
            print(f"错误: {e}")
            return []



    def insert_to_latex(self, latex_file, output_file=None, bib_list=None):
        """
        将bib条目平均分配插入到LaTeX论文的\cite{}或\citep{}中
        确保每个bib条目只被插入一次,如果已存在则跳过

        参数:
            latex_file: LaTeX论文文件路径
            output_file: 输出文件路径(如果为None,则覆盖原文件)
            bib_list: 要插入的bib列表(如果为None,使用当前加载的列表)

        返回:
            修改后的LaTeX内容
        """
        # 使用指定的bib_list或默认的self.bib_list
        bibs_to_insert = bib_list if bib_list is not None else self.bib_list

        if not bibs_to_insert:
            print("错误: 没有可插入的bib条目")
            return None

        try:
            # 读取LaTeX文件
            with open(latex_file, 'r', encoding='utf-8') as f:
                latex_content = f.read()

            # 从bib_list提取所有cite key
            cite_keys = []
            for bib in bibs_to_insert:
                cite_key_match = re.search(r'@\w+\s*\{\s*([^,\s]+)', bib)
                if cite_key_match:
                    cite_keys.append(cite_key_match.group(1))

            if not cite_keys:
                print("警告: 没有找到有效的cite key")
                return latex_content

            # 找到所有cite命令
            cite_pattern = r'\\(cite[pt]?\*?)\{([^}]*)\}'
            cite_matches = list(re.finditer(cite_pattern, latex_content))

            if not cite_matches:
                print("警告: LaTeX文件中没有找到\\cite或\\citep命令")
                return latex_content

            # 收集所有已经存在的cite key
            existing_keys = set()
            for match in cite_matches:
                old_keys = match.group(2).strip()
                if old_keys:
                    keys = [k.strip() for k in old_keys.split(',')]
                    existing_keys.update(keys)

            # 过滤掉已经存在的cite key
            available_bibs = [k for k in cite_keys if k not in existing_keys]

            num_cites = len(cite_matches)
            num_bibs = len(available_bibs)

            print(f"\n找到 {num_cites} 个cite命令")
            print(f"总共 {len(cite_keys)} 个bib条目, 其中 {len(cite_keys) - num_bibs} 个已存在, {num_bibs} 个需要插入")

            if num_bibs == 0:
                print("✓ 所有bib条目都已存在,无需插入")
                return latex_content

            # 平均分配策略
            bibs_per_cite = num_bibs // num_cites
            remainder = num_bibs % num_cites

            # 分配bib到各个cite
            bib_assignments = []
            bib_index = 0

            for i in range(num_cites):
                count = bibs_per_cite + (1 if i < remainder else 0)
                assigned_bibs = available_bibs[bib_index:bib_index + count]
                bib_assignments.append(assigned_bibs)
                bib_index += count

            # 从后往前替换,避免位置偏移
            modified_content = latex_content
            offset = 0

            print(f"\n插入详情:")
            for i, match in enumerate(cite_matches):
                cite_cmd = match.group(1)
                old_keys = match.group(2).strip()
                assigned_bibs = bib_assignments[i]

                if not assigned_bibs:
                    continue

                # 构建新的cite内容
                new_bibs_str = ','.join(assigned_bibs)
                if old_keys:
                    new_content = f'\\{cite_cmd}{{{old_keys},{new_bibs_str}}}'
                else:
                    new_content = f'\\{cite_cmd}{{{new_bibs_str}}}'

                # 替换
                start = match.start() + offset
                end = match.end() + offset
                modified_content = modified_content[:start] + new_content + modified_content[end:]
                offset += len(new_content) - (end - start)

                print(f"  [{i + 1}] 插入 {len(assigned_bibs)} 个: {new_bibs_str}")

            # 保存结果
            if output_file is None:
                output_file = latex_file

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(modified_content)

            print(f"\n✓ 成功将 {num_bibs} 个新bib条目平均分配到cite命令中")
            print(f"  输出文件: {output_file}")

            return modified_content

        except FileNotFoundError:
            print(f"错误: 找不到文件 '{latex_file}'")
            return None
        except Exception as e:
            print(f"错误: {e}")
            return None

    def save_bib_list(self, output_file):
        """
        将当前的bib列表保存到文件

        参数:
            output_file: 输出文件路径
        """
        if not self.bib_list:
            print("错误: 没有可保存的bib条目")
            return False

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(self.bib_list))
            print(f"✓ 已保存 {len(self.bib_list)} 个bib条目到 {output_file}")
            return True
        except Exception as e:
            print(f"错误: {e}")
            return False


# 使用示例
if __name__ == "__main__":
    # 创建管理器实例
    manager = BibTeXManager()

    # 1. 提取bib条目
    manager.extract_bib_entries(fr"example_data\bib.txt")
    print(manager.bib_list)
    print(manager.cite_keys)

    # 3. 插入到LaTeX文件
    manager.insert_to_latex(
        latex_file="example_data\sample.tex",
        output_file="example_data\paper_modified.tex"
    )

    manager.save_bib_list("example_data\output.txt")


