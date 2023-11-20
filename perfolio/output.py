class Output:
    text_callback = None
    table_callback = None

    def register_callbacks(self, text_callback, table_callback):
        self.text_callback = text_callback
        self.table_callback = table_callback

    def log_text(self, text: str):
        self.text_callback(text)

    def log_table(self, name: str, headers: list[str], data: list[tuple]):
        self.table_callback(name, headers, data)
        