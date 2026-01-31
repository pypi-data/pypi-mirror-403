from pathlib import Path

import pandas as pd
import win32com.client as win32


def remove_underscores_from_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.replace("_", " ")
    return df


def get_excel_files_from_folder(folder: str) -> list[str]:
    return [str(f.resolve()) for f in Path(folder).glob("*") if f.suffix == ".xlsx"]


def combine_excel_files(out_path: str, files: list[str] = None, overwrite: bool = True):
    out_path = Path(out_path)

    if overwrite:
        if out_path.exists():
            out_path.unlink()

    # INITIALIZE EXCEL COM APP
    try:
        xlapp = win32.gencache.EnsureDispatch("Excel.Application")

        # constants
        xlPasteValues = -4163
        lPasteFormats = -4122
        xlWorkbookDefault = 51

        # create new workbook
        new_wb = xlapp.Workbooks.Add()
        new_wb.SaveAs(Filename=str(out_path), FileFormat=xlWorkbookDefault)

        dup_count = 1

        for wb in files:
            xlwb = xlapp.Workbooks.Open(wb)

            for xlsh in xlwb.Worksheets:
                new_sh = new_wb.Worksheets.Add()

                try:
                    new_sh.Name = xlsh.Name

                # Ugly non defined exception. Be aware that this wil caputre
                except Exception as e:
                    new_sh.Name = f"{xlsh.Name}_{dup_count}"
                    dup_count += 1

                new_wb.Save()
                new_sh.Move(After=new_wb.Worksheets(new_wb.Worksheets.Count))

                xlsh.Cells.Copy(new_sh.Cells)
                new_sh = None

            xlwb.Close(True)
            xlwb = None

        # remove default blad1
        new_wb.Worksheets("Blad1").Delete()
        new_wb.Save()

    except Exception as e:
        print(e)

    # RELEASE RESOURCES
    finally:
        xlsh = None
        new_sh = None
        xlwb = None
        new_wb = None
        xlapp.Quit()
        xlapp = None
        xlwb = None
