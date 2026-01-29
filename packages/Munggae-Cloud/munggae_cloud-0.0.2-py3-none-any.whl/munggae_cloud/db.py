import json
import os

class JsonDB:
    """딕셔너리처럼 사용하면 자동으로 JSON 파일에 저장되는 간단한 DB"""
    def __init__(self, path: str = "database.json"):
        self.path = path
        self.data = self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def set(self, key: str, value):
        """데이터를 저장하거나 수정합니다"""
        self.data[str(key)] = value
        self._save()

    def get(self, key: str, default=None):
        """
        데이터를 가져옵니다
        만약 없으면 default 값을 반환합니다
        """
        return self.data.get(str(key), default)

    def delete(self, key: str):
        """데이터를 삭제합니다"""
        if str(key) in self.data:
            del self.data[str(key)]
            self._save()
            return True
        return False
        
    def all(self):
        """모든 데이터를 반환합니다"""
        return self.data