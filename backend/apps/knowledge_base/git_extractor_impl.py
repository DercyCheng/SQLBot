"""
Git仓库提取器 - 具体实现示例
展示如何从GitHub/GitLab等代码仓库提取知识
"""

import os
import re
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import json

# 这些是假设的导入，实际项目中需要调整
# from git import Repo  # GitPython
# from tree_sitter import Language, Parser  # tree-sitter
# from pygments.lexers import get_lexer_by_name


@dataclass
class CodeSymbol:
    """代码符号（函数、类等）"""
    name: str
    symbol_type: str  # function, class, method, variable
    start_line: int
    end_line: int
    docstring: str = ""
    signature: str = ""
    parent: Optional[str] = None  # 父类或模块


@dataclass
class CodeFile:
    """代码文件信息"""
    file_path: str
    language: str
    symbols: List[CodeSymbol]
    imports: List[str]
    size: int
    lines: int


class LanguageDetector:
    """编程语言检测器"""
    
    LANGUAGE_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
        '.cpp': 'cpp',
        '.c': 'c',
        '.cs': 'csharp',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
    }
    
    @classmethod
    def detect_language(cls, file_path: str) -> Optional[str]:
        """根据文件扩展名检测语言"""
        ext = Path(file_path).suffix.lower()
        return cls.LANGUAGE_EXTENSIONS.get(ext)
    
    @classmethod
    def is_code_file(cls, file_path: str) -> bool:
        """检查是否是代码文件"""
        return cls.detect_language(file_path) is not None
    
    @classmethod
    def is_doc_file(cls, file_path: str) -> bool:
        """检查是否是文档文件"""
        doc_extensions = {'.md', '.rst', '.txt', '.asciidoc', '.adoc'}
        ext = Path(file_path).suffix.lower()
        return ext in doc_extensions


class CodeParser:
    """代码解析器 - 支持多语言"""
    
    # 简单的正则表达式解析器（实际项目中应使用tree-sitter）
    
    # Python解析规则
    PYTHON_FUNCTION = re.compile(
        r'^\s*(?:async\s+)?def\s+(\w+)\s*\((.*?)\).*?:',
        re.MULTILINE
    )
    PYTHON_CLASS = re.compile(
        r'^\s*class\s+(\w+)(?:\((.*?)\))?:',
        re.MULTILINE
    )
    PYTHON_IMPORT = re.compile(
        r'^\s*(?:from|import)\s+(.+?)(?:\s+import)?.*$',
        re.MULTILINE
    )
    PYTHON_DOCSTRING = re.compile(
        r'^\s+"""(.*?)"""',
        re.MULTILINE | re.DOTALL
    )
    
    @classmethod
    async def parse(cls, file_path: str, content: str, language: str) -> CodeFile:
        """解析代码文件"""
        
        if language == 'python':
            return await cls._parse_python(file_path, content)
        elif language in ['javascript', 'typescript']:
            return await cls._parse_javascript(file_path, content)
        elif language == 'java':
            return await cls._parse_java(file_path, content)
        elif language == 'go':
            return await cls._parse_go(file_path, content)
        else:
            # 通用解析 - 仅提取注释和导入
            return await cls._parse_generic(file_path, content, language)
    
    @classmethod
    async def _parse_python(cls, file_path: str, content: str) -> CodeFile:
        """Python代码解析"""
        symbols = []
        lines_list = content.split('\n')
        
        # 提取函数
        for match in cls.PYTHON_FUNCTION.finditer(content):
            func_name = match.group(1)
            params = match.group(2)
            start_line = content[:match.start()].count('\n') + 1
            
            # 查找docstring
            docstring = ""
            match_idx = match.end()
            if match_idx < len(content):
                doc_match = cls.PYTHON_DOCSTRING.search(content[match_idx:])
                if doc_match:
                    docstring = doc_match.group(1).strip()
            
            symbols.append(CodeSymbol(
                name=func_name,
                symbol_type='function',
                start_line=start_line,
                end_line=start_line + 10,  # 简化处理
                docstring=docstring,
                signature=f"def {func_name}({params})"
            ))
        
        # 提取类
        for match in cls.PYTHON_CLASS.finditer(content):
            class_name = match.group(1)
            bases = match.group(2) or ""
            start_line = content[:match.start()].count('\n') + 1
            
            symbols.append(CodeSymbol(
                name=class_name,
                symbol_type='class',
                start_line=start_line,
                end_line=start_line + 20,
                signature=f"class {class_name}({bases})"
            ))
        
        # 提取导入
        imports = []
        for match in cls.PYTHON_IMPORT.finditer(content):
            imports.append(match.group(1).strip())
        
        return CodeFile(
            file_path=file_path,
            language='python',
            symbols=symbols,
            imports=imports,
            size=len(content),
            lines=len(lines_list)
        )
    
    @classmethod
    async def _parse_javascript(cls, file_path: str, content: str) -> CodeFile:
        """JavaScript/TypeScript解析（简化版）"""
        # TODO: 实现实际的JS解析
        
        symbols = []
        
        # 简单的函数匹配
        func_pattern = re.compile(
            r'(?:async\s+)?(?:function|const|let|var)\s+(\w+)\s*(?:=\s*(?:async\s*)?\(|\()',
            re.MULTILINE
        )
        
        for match in func_pattern.finditer(content):
            name = match.group(1)
            start_line = content[:match.start()].count('\n') + 1
            symbols.append(CodeSymbol(
                name=name,
                symbol_type='function',
                start_line=start_line,
                end_line=start_line + 5
            ))
        
        # 提取导入
        import_pattern = re.compile(
            r'^\s*(?:import|from).*',
            re.MULTILINE
        )
        imports = [m.group(0) for m in import_pattern.finditer(content)]
        
        return CodeFile(
            file_path=file_path,
            language='javascript',
            symbols=symbols,
            imports=imports,
            size=len(content),
            lines=len(content.split('\n'))
        )
    
    @classmethod
    async def _parse_java(cls, file_path: str, content: str) -> CodeFile:
        """Java代码解析（简化版）"""
        # TODO: 实现Java解析
        return CodeFile(
            file_path=file_path,
            language='java',
            symbols=[],
            imports=[],
            size=len(content),
            lines=len(content.split('\n'))
        )
    
    @classmethod
    async def _parse_go(cls, file_path: str, content: str) -> CodeFile:
        """Go代码解析（简化版）"""
        # TODO: 实现Go解析
        return CodeFile(
            file_path=file_path,
            language='go',
            symbols=[],
            imports=[],
            size=len(content),
            lines=len(content.split('\n'))
        )
    
    @classmethod
    async def _parse_generic(cls, file_path: str, content: str, 
                            language: str) -> CodeFile:
        """通用代码解析"""
        return CodeFile(
            file_path=file_path,
            language=language,
            symbols=[],
            imports=[],
            size=len(content),
            lines=len(content.split('\n'))
        )


class GitRepositoryScanner:
    """Git仓库扫描器"""
    
    # 应该忽略的目录
    IGNORE_DIRS = {
        '.git', '.gitignore', '__pycache__', 'node_modules',
        '.venv', 'venv', '.env', 'dist', 'build', '.next',
        '.nuxt', '.cache', 'target', 'bin', 'obj',
    }
    
    # 应该忽略的文件
    IGNORE_FILES = {
        '.gitignore', '.gitattributes', '.DS_Store', 'thumbs.db',
    }
    
    @classmethod
    def should_ignore(cls, path: str) -> bool:
        """检查路径是否应该被忽略"""
        path_parts = Path(path).parts
        
        # 检查目录
        for part in path_parts:
            if part in cls.IGNORE_DIRS:
                return True
        
        # 检查文件
        name = Path(path).name
        if name in cls.IGNORE_FILES:
            return True
        
        return False
    
    @classmethod
    async def scan_directory(cls, root_path: str, config: Dict[str, Any]) -> List[str]:
        """
        扫描目录，返回相关文件列表
        
        Args:
            root_path: 根路径
            config: 配置信息
                - file_patterns: 文件模式列表，e.g., ['*.py', '*.md']
                - exclude_patterns: 排除模式
                - max_depth: 最大深度
        
        Returns:
            文件路径列表
        """
        
        file_patterns = config.get('file_patterns', ['*.py', '*.md', '*.js'])
        max_depth = config.get('max_depth', 10)
        
        # 编译glob模式
        import fnmatch
        
        files = []
        
        for root, dirs, filenames in os.walk(root_path):
            # 计算深度
            depth = root.replace(root_path, '').count(os.sep)
            if depth > max_depth:
                continue
            
            # 过滤目录
            dirs[:] = [d for d in dirs if not cls.should_ignore(os.path.join(root, d))]
            
            # 过滤文件
            for filename in filenames:
                file_path = os.path.join(root, filename)
                
                # 检查是否应该忽略
                if cls.should_ignore(file_path):
                    continue
                
                # 检查文件模式
                matches = any(
                    fnmatch.fnmatch(filename, pattern)
                    for pattern in file_patterns
                )
                
                if matches:
                    files.append(file_path)
        
        return files
    
    @classmethod
    async def extract_repo_structure(cls, repo_path: str) -> Dict[str, Any]:
        """
        提取仓库的基本结构信息
        
        Returns:
        {
            "languages": ["python", "javascript", ...],
            "file_count": 123,
            "total_size": 1024000,
            "main_files": ["README.md", "setup.py", ...],
            "directory_structure": {...}
        }
        """
        
        structure = {
            "languages": set(),
            "file_count": 0,
            "total_size": 0,
            "main_files": [],
            "directory_structure": {}
        }
        
        for root, dirs, files in os.walk(repo_path):
            # 过滤目录
            dirs[:] = [d for d in dirs if not cls.should_ignore(os.path.join(root, d))]
            
            for filename in files:
                if cls.should_ignore(os.path.join(root, filename)):
                    continue
                
                file_path = os.path.join(root, filename)
                
                # 统计语言
                language = LanguageDetector.detect_language(filename)
                if language:
                    structure["languages"].add(language)
                
                # 统计文件和大小
                structure["file_count"] += 1
                structure["total_size"] += os.path.getsize(file_path)
                
                # 记录主要文件
                if filename.lower() in ['readme.md', 'setup.py', 'package.json', 'go.mod']:
                    rel_path = os.path.relpath(file_path, repo_path)
                    structure["main_files"].append(rel_path)
        
        structure["languages"] = list(structure["languages"])
        
        return structure


class DocumentationExtractor:
    """文档提取器"""
    
    @classmethod
    async def extract_readme(cls, repo_path: str) -> Optional[Tuple[str, str]]:
        """
        提取README文件
        
        Returns:
            (文件名, 内容)
        """
        readme_names = ['README.md', 'README.rst', 'README.txt', 'README']
        
        for name in readme_names:
            path = os.path.join(repo_path, name)
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return (name, content)
                except Exception as e:
                    print(f"Error reading {path}: {e}")
        
        return None
    
    @classmethod
    async def extract_docs(cls, repo_path: str, docs_dir: str = 'docs') -> Dict[str, str]:
        """
        提取docs目录下的文档
        
        Returns:
            {文件路径: 内容}
        """
        docs_path = os.path.join(repo_path, docs_dir)
        docs = {}
        
        if not os.path.exists(docs_path):
            return docs
        
        for root, dirs, files in os.walk(docs_path):
            for filename in files:
                if LanguageDetector.is_doc_file(filename):
                    file_path = os.path.join(root, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        rel_path = os.path.relpath(file_path, repo_path)
                        docs[rel_path] = content
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
        
        return docs


class GitExtractorImpl:
    """Git提取器 - 完整实现"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.repo_path = None
    
    async def extract(self) -> Dict[str, Any]:
        """
        从Git仓库提取知识
        
        Returns:
        {
            "documents": [
                {
                    "type": "code",
                    "file_path": "src/main.py",
                    "language": "python",
                    "content": "def foo(): ...",
                    "symbols": [...],
                    "imports": [...]
                },
                {
                    "type": "document",
                    "file_path": "README.md",
                    "content": "# Project ..."
                }
            ],
            "metadata": {
                "repo_url": "...",
                "languages": [...],
                "structure": {...}
            }
        }
        """
        
        # 1. 获取或克隆仓库
        await self._setup_repository()
        
        # 2. 扫描代码文件
        documents = []
        
        # 扫描代码文件
        code_files = await GitRepositoryScanner.scan_directory(
            self.repo_path,
            self.config
        )
        
        for file_path in code_files:
            try:
                doc = await self._process_file(file_path)
                if doc:
                    documents.append(doc)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        # 3. 提取文档
        readme = await DocumentationExtractor.extract_readme(self.repo_path)
        if readme:
            documents.append({
                "type": "document",
                "file_path": readme[0],
                "content": readme[1],
                "language": "markdown"
            })
        
        docs = await DocumentationExtractor.extract_docs(self.repo_path)
        for doc_path, content in docs.items():
            documents.append({
                "type": "document",
                "file_path": doc_path,
                "content": content,
                "language": "markdown"
            })
        
        # 4. 获取仓库结构
        structure = await GitRepositoryScanner.extract_repo_structure(self.repo_path)
        
        return {
            "documents": documents,
            "metadata": {
                "repo_url": self.config.get('repo_url'),
                "branch": self.config.get('branch', 'main'),
                **structure
            }
        }
    
    async def _setup_repository(self):
        """初始化仓库（克隆或更新）"""
        # TODO: 实现Git克隆/更新逻辑
        # 这里应该使用GitPython
        # from git import Repo
        # repo = Repo.clone_from(self.config['repo_url'], local_path)
        
        # 简化处理：假设已有本地路径
        self.repo_path = self.config.get('local_path', '/tmp/repo')
    
    async def _process_file(self, file_path: str) -> Optional[Dict]:
        """处理单个文件"""
        
        # 检测语言
        language = LanguageDetector.detect_language(file_path)
        
        if not language:
            return None
        
        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
        
        # 解析代码
        try:
            parsed = await CodeParser.parse(file_path, content, language)
            
            rel_path = os.path.relpath(file_path, self.repo_path)
            
            return {
                "type": "code",
                "file_path": rel_path,
                "language": language,
                "content": content,
                "symbols": [asdict(s) for s in parsed.symbols],
                "imports": parsed.imports,
                "line_count": parsed.lines,
                "size": parsed.size
            }
        
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None


# 使用示例
async def example_usage():
    """使用示例"""
    
    config = {
        "repo_url": "https://github.com/user/project.git",
        "branch": "main",
        "local_path": "/tmp/project",
        "file_patterns": ["*.py", "*.md"],
        "max_depth": 5
    }
    
    extractor = GitExtractorImpl(config)
    result = await extractor.extract()
    
    print(f"Extracted {len(result['documents'])} documents")
    print(f"Supported languages: {result['metadata']['languages']}")
    print(f"File count: {result['metadata']['file_count']}")
    
    # 输出第一个代码文件的信息
    for doc in result['documents']:
        if doc['type'] == 'code':
            print(f"\nFile: {doc['file_path']}")
            print(f"Language: {doc['language']}")
            print(f"Lines: {doc['line_count']}")
            print(f"Symbols: {len(doc['symbols'])}")
            if doc['symbols']:
                print(f"  - {doc['symbols'][0]['name']}")
            break


if __name__ == "__main__":
    # python -m asyncio
    # asyncio.run(example_usage())
    pass
