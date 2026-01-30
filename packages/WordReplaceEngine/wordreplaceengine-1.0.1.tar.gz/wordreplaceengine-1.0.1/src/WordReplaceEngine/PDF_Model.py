#coding=UTF-8
"""
    WordReplaceEngine
    Copyright (C) 2026 Yun-De Huang <startime_electronics@orztrickster.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

try:
    import os
    import sys
    import json
except:
    pass

class PDF_Model():
    """
    MIT License

    Copyright (c) 2020 Al Johri

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
    """

    def __init__(self):
        import subprocess
        from pathlib import Path
        self.subprocess = subprocess
        self.Path = Path

    def windows(self, paths, keep_active):
        try:
            if not hasattr(self, 'word'):
                import pythoncom
                import win32com.client
                pythoncom.CoInitialize() # 初始化 COM 環境(非必要)
                self.word = win32com.client.DispatchEx("Word.Application")
            wdFormatPDF = 17

            if paths["batch"]:
                for docx_filepath in sorted(self.Path(paths["input"]).glob("[!~]*.doc*")):
                    pdf_filepath = self.Path(paths["output"]) / (str(docx_filepath.stem) + ".pdf")
                    doc = self.word.Documents.Open(str(docx_filepath))
                    doc.SaveAs(str(pdf_filepath), FileFormat=wdFormatPDF)
                    doc.Close(0)
            else:
                docx_filepath = self.Path(paths["input"]).resolve()
                pdf_filepath = self.Path(paths["output"]).resolve()
                doc = self.word.Documents.Open(str(docx_filepath))
                doc.SaveAs(str(pdf_filepath), FileFormat=wdFormatPDF)
                doc.Close(0)

            if not keep_active and hasattr(self, 'word'):
                self.word.Quit()
                del self.word
                pythoncom.CoUninitialize()# 釋放 COM 環境(非必要)
        except Exception as e:
            print(rf"PDF輸出失敗!!! --> {e}")

    def macos(self, paths, keep_active):
        script = (self.Path(__file__).parent / "convert.jxa").resolve()
        cmd = [
            "/usr/bin/osascript",
            "-l",
            "JavaScript",
            str(script),
            str(paths["input"]),
            str(paths["output"]),
            str(keep_active).lower(),
        ]

        def run(cmd):
            process = self.subprocess.Popen(cmd, stderr=self.subprocess.PIPE)
            while True:
                line = process.stderr.readline().rstrip()
                if not line:
                    break
                yield line.decode("utf-8")

        total = len(list(self.Path(paths["input"]).glob("*.doc*"))) if paths["batch"] else 1

        for line in run(cmd):
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if msg["result"] == "success":
                pass
            elif msg["result"] == "error":
                print(msg)
                sys.exit(1)


    def resolve_paths(self, input_path, output_path):
        input_path = self.Path(input_path).resolve()
        output_path = self.Path(output_path).resolve() if output_path else None
        output = {}
        if input_path.is_dir():
            output["batch"] = True
            output["input"] = str(input_path)
            if output_path:
                assert output_path.is_dir()
            else:
                output_path = str(input_path)
            output["output"] = output_path
        else:
            output["batch"] = False
            assert str(input_path).endswith((".docx", ".DOCX", ".doc", ".DOC"))
            output["input"] = str(input_path)
            if output_path and output_path.is_dir():
                output_path = str(output_path / (str(input_path.stem) + ".pdf"))
            elif output_path:
                assert str(output_path).endswith(".pdf")
            else:
                output_path = str(input_path.parent / (str(input_path.stem) + ".pdf"))
            output["output"] = output_path
        return output


    def convert(self, input_path, output_path=None, keep_active=False):
        paths = self.resolve_paths(input_path, output_path)
        if sys.platform == "darwin":
            return self.macos(paths, keep_active)
        elif sys.platform == "win32":
            return self.windows(paths, keep_active)
        else:
            raise NotImplementedError(
                "docx2pdf is not implemented for linux as it requires Microsoft Word to be installed"
            )
    def closure(self):
        if hasattr(self, 'word'):
            try:
                self.word.Quit()
            except:
                pass
            del self.word

    def cli(self):

        import textwrap
        import argparse

        if "--version" in sys.argv:
            sys.exit(0)

        description = textwrap.dedent(
            """
        Example Usage:

        Convert single docx file in-place from myfile.docx to myfile.pdf:
            docx2pdf myfile.docx

        Batch convert docx folder in-place. Output PDFs will go in the same folder:
            docx2pdf myfolder/

        Convert single docx file with explicit output filepath:
            docx2pdf input.docx output.docx

        Convert single docx file and output to a different explicit folder:
            docx2pdf input.docx output_dir/

        Batch convert docx folder. Output PDFs will go to a different explicit folder:
            docx2pdf input_dir/ output_dir/
        """
        )

        formatter_class = lambda prog: argparse.RawDescriptionHelpFormatter(
            prog, max_help_position=32
        )
        parser = argparse.ArgumentParser(
            description=description, formatter_class=formatter_class
        )
        parser.add_argument(
            "input",
            help="input file or folder. batch converts entire folder or convert single file",
        )
        parser.add_argument("output", nargs="?", help="output file or folder")
        parser.add_argument(
            "--keep-active",
            action="store_true",
            default=False,
            help="prevent closing word after conversion",
        )
        parser.add_argument(
            "--version", action="store_true", default=False, help="display version and exit"
        )

        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(0)
        else:
            args = parser.parse_args()

        self.convert(args.input, args.output, args.keep_active)

    def __del__(self):
        try:
            if hasattr(self, 'word'):
                try:
                    self.word.Quit()
                except:
                    pass
                del self.word
        except Exception as e:
            print(f"__del__ 發生例外：{e}")











class PDF_Model_Syncfusion():
    def __init__(self, syncfusion_key = None):
        self.syncfusion_key = syncfusion_key
        if self.syncfusion_key is None:
            raise
        import os
        import sys
        from pathlib import Path
        import clr
        

        self.os = os
        self.sys = sys
        self.Path = Path
        self.clr = clr
        


        base_dir = self.Path(getattr(self.sys, "_MEIPASS", self.Path(__file__).parent))
        bundle_dir = base_dir / "syncfusion"
        if bundle_dir.exists():
            self.syncfusion_dll_path = str(bundle_dir)
        else:
            self.syncfusion_dll_path = r"C:\Program Files (x86)\Syncfusion\Essential Studio\Document SDK\31.1.17\Assemblies\4.6.2"

        self.sys.path.append(self.syncfusion_dll_path)
        self.os.environ["PATH"] = self.syncfusion_dll_path + self.os.pathsep + self.os.environ.get("PATH", "")


        def add_ref(name):
            p = self.Path(self.syncfusion_dll_path) / f"{name}.dll"
            if not p.exists():
                raise FileNotFoundError(f"缺少 {p}")
            clr.AddReference(str(p))


        try:
            add_ref("Syncfusion.Licensing")
            from Syncfusion.Licensing import SyncfusionLicenseProvider
            SyncfusionLicenseProvider.RegisterLicense(self.syncfusion_key)
        except Exception as e:
            print("Licensing 可略過測試：", e)


        for name in [
            "Syncfusion.DocIO.Base",
            "Syncfusion.Compression.Base",
            "Syncfusion.OfficeChart.Base",
            "Syncfusion.Pdf.Base",
            "Syncfusion.DocToPDFConverter.Base", 
        ]:
            add_ref(name)


        from Syncfusion.DocIO.DLS import WordDocument
        from Syncfusion.DocIO import FormatType
        from Syncfusion.DocToPDFConverter import DocToPDFConverter


        self.WordDocument = WordDocument
        self.FormatType = FormatType
        self.DocToPDFConverter = DocToPDFConverter

    def convert(self, input_path, output_path):
        if self.syncfusion_key is None:
            raise
        def guess_format(path: str):
            ext = self.Path(path).suffix.lower()
            if ext == ".docx":
                return self.FormatType.Docx
            elif ext == ".doc":
                return self.FormatType.Doc
            elif ext == ".rtf":
                return self.FormatType.Rtf
            else:
                return self.FormatType.Docx

        def word_to_pdf(input_docx, output_pdf):
            fmt = guess_format(input_docx)
            doc = self.WordDocument(str(input_docx), fmt)
            try:
                converter = self.DocToPDFConverter()
                pdf = converter.ConvertToPDF(doc)
                pdf.Save(str(output_pdf))
                pdf.Close(True)
            finally:
                doc.Close()

        word_to_pdf(input_path, output_path)



