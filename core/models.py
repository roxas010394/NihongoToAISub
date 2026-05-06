class SubtitleLine:
    def __init__(self, start_time, end_time, text, style="Default"):
        self.start =start_time
        self.end = end_time
        self.text = text
        self.style = style
    @staticmethod
    def format_time(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int(round((seconds - int(seconds)) * 100))
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"