using System;
using System.Drawing;
using System.Globalization;
using System.Windows.Forms;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.Geometry;
using Autodesk.AutoCAD.Runtime;
using CadApp = Autodesk.AutoCAD.ApplicationServices.Application;

[assembly: CommandClass(typeof(CodexAutoCAD.RectangleCommands))]

namespace CodexAutoCAD
{
    public sealed class RectangleCommands
    {
        [CommandMethod("CODEXRECT", CommandFlags.Modal)]
        public void DrawRectangle()
        {
            var doc = CadApp.DocumentManager.MdiActiveDocument;
            var ucs = doc.Editor.CurrentUserCoordinateSystem;
            using (var dialog = new RectangleDialog())
            {
                DialogResult choice = CadApp.ShowModalDialog(dialog);
                if (choice != DialogResult.OK)
                {
                    doc.Editor.WriteMessage("\nCODEXRECT: cancelled.");
                    return;
                }

                try
                {
                    var id = ApplyChoice(doc.Database, ucs, choice, dialog.Values);
                    doc.Editor.WriteMessage("\nCODEXRECT: created handle {0}.", id.Handle);
                }
                catch (Autodesk.AutoCAD.Runtime.Exception error)
                {
                    doc.Editor.WriteMessage("\nCODEXRECT: drawing failed: {0}.", error.Message);
                }
                catch (InvalidOperationException error)
                {
                    doc.Editor.WriteMessage("\nCODEXRECT: {0}", error.Message);
                }
            }
        }

        [CommandMethod("CODEXRECTCHECK", CommandFlags.Modal)]
        public void CheckRectangle()
        {
            var editor = CadApp.DocumentManager.MdiActiveDocument.Editor;
            using (var sample = new Database(true, true))
            {
                var input = new RectangleValues(2, 3, 8, 5);
                var cancelled = ApplyChoice(sample, Matrix3d.Identity, DialogResult.Cancel, input);
                var ucs = Matrix3d.Rotation(Math.PI / 2, Vector3d.ZAxis, Point3d.Origin);
                var created = ApplyChoice(sample, ucs, DialogResult.OK, input);
                using (var tx = sample.TransactionManager.StartOpenCloseTransaction())
                {
                    var space = (BlockTableRecord)tx.GetObject(sample.CurrentSpaceId, OpenMode.ForRead);
                    int count = 0;
                    foreach (ObjectId id in space) count++;
                    var rect = (Polyline)tx.GetObject(created, OpenMode.ForRead);
                    bool ok = cancelled.IsNull && count == 1 && rect.Closed && rect.NumberOfVertices == 4
                        && Math.Abs(rect.Area - 40) < 1e-8
                        && rect.GetPoint3dAt(0).DistanceTo(new Point3d(-3, 2, 0)) < 1e-8;
                    editor.WriteMessage(ok ? "\nCODEXRECTCHECK: PASS\n" : "\nCODEXRECTCHECK: FAIL\n");
                }
            }
        }

        private static ObjectId ApplyChoice(Database db, Matrix3d ucs, DialogResult choice, RectangleValues values)
        {
            if (choice != DialogResult.OK) return ObjectId.Null;
            if (!values.IsValid) throw new InvalidOperationException("Enter valid rectangle dimensions.");

            using (var tx = db.TransactionManager.StartTransaction())
            {
                var layer = (LayerTableRecord)tx.GetObject(db.Clayer, OpenMode.ForRead);
                if (layer.IsLocked) throw new InvalidOperationException("The current layer is locked.");
                var space = (BlockTableRecord)tx.GetObject(db.CurrentSpaceId, OpenMode.ForWrite);
                using (var rect = new Polyline(4))
                {
                    rect.SetDatabaseDefaults(db);
                    double x = values.X, y = values.Y;
                    rect.AddVertexAt(0, new Point2d(x, y), 0, 0, 0);
                    rect.AddVertexAt(1, new Point2d(x + values.Width, y), 0, 0, 0);
                    rect.AddVertexAt(2, new Point2d(x + values.Width, y + values.Height), 0, 0, 0);
                    rect.AddVertexAt(3, new Point2d(x, y + values.Height), 0, 0, 0);
                    rect.Closed = true;
                    rect.TransformBy(ucs);
                    var id = space.AppendEntity(rect);
                    tx.AddNewlyCreatedDBObject(rect, true);
                    tx.Commit();
                    return id;
                }
            }
        }
    }

    internal struct RectangleValues
    {
        internal readonly double X, Y, Width, Height;

        internal RectangleValues(double x, double y, double width, double height)
        {
            X = x;
            Y = y;
            Width = width;
            Height = height;
        }

        internal bool IsValid
        {
            get
            {
                return Finite(X) && Finite(Y) && Finite(Width) && Finite(Height)
                    && Finite(X + Width) && Finite(Y + Height) && Finite(Width * Height)
                    && Width * Height > 0 && Width > 0 && Height > 0
                    && X + Width > X && Y + Height > Y;
            }
        }

        private static bool Finite(double value)
        {
            return !double.IsNaN(value) && !double.IsInfinity(value);
        }
    }

    internal sealed class RectangleDialog : Form
    {
        private readonly TextBox x, y, width, height;
        private readonly Label error;
        internal RectangleValues Values { get; private set; }

        internal RectangleDialog()
        {
            Text = "Codex 矩形绘图";
            ClientSize = new Size(400, 224);
            StartPosition = FormStartPosition.CenterParent;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            MinimizeBox = false;
            ShowInTaskbar = false;
            AutoScaleMode = AutoScaleMode.Font;

            var grid = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(14), ColumnCount = 2 };
            grid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 43));
            grid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 57));
            Controls.Add(grid);
            x = AddField(grid, "基点 X（UCS）", "0");
            y = AddField(grid, "基点 Y（UCS）", "0");
            width = AddField(grid, "宽度", "4");
            height = AddField(grid, "高度", "3");
            error = new Label { AutoSize = true, ForeColor = Color.Firebrick, Margin = new Padding(3, 6, 3, 6) };
            grid.Controls.Add(error);
            grid.SetColumnSpan(error, 2);

            var buttons = new FlowLayoutPanel { Dock = DockStyle.Fill, AutoSize = true, FlowDirection = System.Windows.Forms.FlowDirection.RightToLeft };
            var cancel = new Button { Text = "取消", DialogResult = DialogResult.Cancel };
            var apply = new Button { Text = "绘制" };
            buttons.Controls.Add(cancel);
            buttons.Controls.Add(apply);
            grid.Controls.Add(buttons);
            grid.SetColumnSpan(buttons, 2);
            AcceptButton = apply;
            CancelButton = cancel;
            apply.Click += Confirm;
        }

        private static TextBox AddField(TableLayoutPanel grid, string label, string initial)
        {
            var field = new TextBox { Text = initial, Dock = DockStyle.Top, AccessibleName = label };
            grid.Controls.Add(new Label { Text = label, AutoSize = true, Anchor = AnchorStyles.Left });
            grid.Controls.Add(field);
            return field;
        }

        private void Confirm(object sender, EventArgs e)
        {
            double xValue, yValue, widthValue, heightValue;
            if (TryNumber(x.Text, out xValue) && TryNumber(y.Text, out yValue)
                && TryNumber(width.Text, out widthValue) && TryNumber(height.Text, out heightValue))
            {
                var values = new RectangleValues(xValue, yValue, widthValue, heightValue);
                if (values.IsValid)
                {
                    Values = values;
                    DialogResult = DialogResult.OK;
                    return;
                }
            }
            error.Text = "请输入有效坐标，以及大于零的宽度和高度。";
        }

        private static bool TryNumber(string text, out double value)
        {
            return double.TryParse(text, NumberStyles.Float, CultureInfo.CurrentCulture, out value)
                || double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out value);
        }
    }
}
