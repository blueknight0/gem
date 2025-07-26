import tkinter as tk
from gui import MainApp

if __name__ == "__main__":
    # 필수 라이브러리 설치 확인 (필요 시 gui나 services에서 처리)
    # 이곳은 순수하게 앱을 실행하는 역할만 담당
    root = tk.Tk()
    app = MainApp(root)
    app.pack(side="top", fill="both", expand=True)
    root.mainloop()
