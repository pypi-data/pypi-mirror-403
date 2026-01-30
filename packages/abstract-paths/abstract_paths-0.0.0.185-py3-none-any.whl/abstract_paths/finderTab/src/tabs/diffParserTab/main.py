from .imports import *
class diffParserTab(QWidget):
    def __init__(self, bus: SharedStateBus):
        super().__init__()
        initFuncs(self)
        root = QVBoxLayout(self)
        # Common inputs (dir, filters, etc.)
        grid = QGridLayout()
        install_common_inputs(
            self, grid, bus=bus,
            default_dir_in=os.getcwd(),
            primary_btn=("Preview", self.preview_patch),
            secondary_btn=("Save", self.save_patch),
            trinary_btn=("Save All", (lambda: self.save_all_checked())),
            default_allowed_exts_in=False,
            default_exclude_dirs_in=True
        )

        # Files tree (match results)
        root.addWidget(QLabel("Files found:"))
        self.files_list = QTreeWidget()
        self.files_list.setColumnCount(3)
        self.files_list.setHeaderLabels(["File", "Apply", "Overwrite"])
        self.files_list.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.files_list.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.files_list.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.files_list.setRootIsDecorated(False)
        # handlers
        self.files_list.itemDoubleClicked.connect(self._open_file_from_row)
        self.files_list.currentItemChanged.connect(lambda *_: self._on_tree_selection_changed())
        root.addWidget(self.files_list, stretch=1)

        # Diff / Preview split
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)

        left = QWidget(); lv = QVBoxLayout(left); lv.setContentsMargins(0,0,0,0)
        lv.addWidget(QLabel("Diff:"))
        self.diff_text = QTextEdit()
        self.diff_text.setPlaceholderText("Paste the diff here...")
        lv.addWidget(self.diff_text, stretch=1)

        right = QWidget(); rv = QVBoxLayout(right); rv.setContentsMargins(0,0,0,0)
        rv.addWidget(QLabel("Preview:"))
        self.preview = QTextEdit(); self.preview.setReadOnly(True)
        rv.addWidget(self.preview, stretch=1)

        self.splitter.addWidget(left)
        self.splitter.addWidget(right)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        root.addWidget(self.splitter, stretch=3)

        # Actions
##        btn_preview = QPushButton("Parse and Preview")
##        btn_preview.clicked.connect(self.preview_patch)
##        root.addWidget(btn_preview)
##
##        btn_save = QPushButton("Approve and Save")
##        btn_save.clicked.connect(self.save_patch)
##        root.addWidget(btn_save)
##        
##        self.saveAllBtn = QPushButton("Approve and Save All")
##        self.saveAllBtn.clicked.connect(lambda: self.save_all_checked()) 
##        root.addWidget(self.saveAllBtn)
        
        # Status line
        self.status_label = QLabel("Ready.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.status_label.setStyleSheet("color: #4caf50; padding: 4px 0;")
        root.addWidget(self.status_label)

    def _preview_for_path(self, target_file: str):
        """Preview ONLY for the provided path (no re-populate / no re-match)."""
        diff = self.diff_text.toPlainText().strip()
        if not diff or not target_file or not os.path.exists(target_file):
            return
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                original_lines = f.read().splitlines()
            patched = apply_custom_diff(original_lines, diff.splitlines())
            self.preview.setPlainText(patched)
            set_status(self, f"Preview generated for: {target_file}", "ok")
            append_log(self, f"Preview generated for {target_file}\n")
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))
            set_status(self, f"Error: {e}", "error")
            append_log(self, f"Error in preview: {e}\n")
        except Exception as e:
            QMessageBox.critical(self, "Unexpected Error", f"An unexpected error occurred: {e}")
            set_status(self, f"Unexpected Error: {e}", "error")
            append_log(self, f"Unexpected error in preview: {e}\n")

    def preview_patch(self):
        diff = self.diff_text.toPlainText().strip()
        if not diff:
            QMessageBox.critical(self, "Error", "No diff provided.")
            set_status(self, "Error: No diff provided.", "error")
            return

        try:
            files = get_files(self)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to gather files: {e}")
            set_status(self, f"Error: {e}", "error")
            return

        if not files:
            QMessageBox.warning(self, "No Files", "No files match the current filters.")
            set_status(self, "No files match filters.", "warn")
            return

        hunks = parse_unified_diff(diff)
        if not hunks:
            QMessageBox.warning(self, "Warning", "No valid hunks found in diff.")
            set_status(self, "No valid hunks found.", "warn")
            return

        matched_files, found_paths = find_matches_for_hunks(files, hunks)

        # Fill the tree. We prefer a flat list of file paths here.
        self._fill_files_tree(matched_files, default_apply=True, default_overwrite=True)

        # Choose preview target:
        path = self._pick_preview_target(files, hunks)
        if not path:
            # fallback to first match if present
            if matched_files:
                path = matched_files[0]
            elif found_paths:
                path = found_paths[0]["file_path"]

        if not path:
            set_status(self, "No matches found in any file.", "warn")
            return

        _preview_for_path(self, path)
