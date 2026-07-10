import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import random
from collections import deque
import heapq
import time
import csv


# =========================
# 全局配置
# =========================

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class MazeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("灵境迷宫 · 智能寻路系统 Plus")

        # 默认参数
        self.N = 21
        self.cell_size = 25
        self.algorithm = "BFS"
        self.animate = True
        self.anim_delay = 15

        # 鼠标模式：wall 设置墙壁；start 设置起点；end 设置终点
        self.edit_mode = "wall"

        self.maze = []
        self.start = (1, 1)
        self.end = (self.N - 2, self.N - 2)

        self.path = []
        self.visited_order = []
        self.last_result = None
        self.last_compare_results = []

        self.create_widgets()
        self.generate_maze()

    # =========================
    # 一、界面设计
    # =========================

    def create_widgets(self):
        title = tk.Label(
            self.root,
            text="灵境迷宫 · 智能寻路系统 Plus",
            font=("微软雅黑", 18, "bold"),
            fg="darkgreen"
        )
        title.pack(pady=8)

        # 第一行：主功能按钮
        ctrl_frame = tk.Frame(self.root)
        ctrl_frame.pack(pady=4)

        tk.Button(ctrl_frame, text="生成新迷宫", command=self.generate_maze).grid(row=0, column=0, padx=4)
        tk.Button(ctrl_frame, text="求解路径", command=self.solve_maze).grid(row=0, column=1, padx=4)
        tk.Button(ctrl_frame, text="清除路径", command=self.clear_path).grid(row=0, column=2, padx=4)
        tk.Button(ctrl_frame, text="算法对比", command=self.compare_algorithms).grid(row=0, column=3, padx=4)
        tk.Button(ctrl_frame, text="导出对比结果", command=self.export_compare_results).grid(row=0, column=4, padx=4)
        tk.Button(ctrl_frame, text="保存迷宫", command=self.save_maze).grid(row=0, column=5, padx=4)
        tk.Button(ctrl_frame, text="加载迷宫", command=self.load_maze).grid(row=0, column=6, padx=4)

        # 第二行：算法选择
        option_frame = tk.Frame(self.root)
        option_frame.pack(pady=4)

        self.algo_var = tk.StringVar(value="BFS")

        tk.Label(option_frame, text="算法选择：").pack(side=tk.LEFT)

        tk.Radiobutton(
            option_frame,
            text="DFS（栈）",
            variable=self.algo_var,
            value="DFS",
            command=self.set_algorithm
        ).pack(side=tk.LEFT, padx=5)

        tk.Radiobutton(
            option_frame,
            text="BFS（队列）",
            variable=self.algo_var,
            value="BFS",
            command=self.set_algorithm
        ).pack(side=tk.LEFT, padx=5)

        tk.Radiobutton(
            option_frame,
            text="A*（优先队列）",
            variable=self.algo_var,
            value="AStar",
            command=self.set_algorithm
        ).pack(side=tk.LEFT, padx=5)

        self.anim_var = tk.IntVar(value=1)
        tk.Checkbutton(
            option_frame,
            text="动画演示",
            variable=self.anim_var,
            command=self.set_animation
        ).pack(side=tk.LEFT, padx=15)

        # 第三行：迷宫大小与编辑模式
        setting_frame = tk.Frame(self.root)
        setting_frame.pack(pady=4)

        tk.Label(setting_frame, text="迷宫大小：").pack(side=tk.LEFT)

        self.size_var = tk.StringVar(value="21")
        size_box = ttk.Combobox(
            setting_frame,
            textvariable=self.size_var,
            values=["15", "21", "31", "41"],
            width=5,
            state="readonly"
        )
        size_box.pack(side=tk.LEFT, padx=5)

        tk.Button(setting_frame, text="应用大小", command=self.apply_size).pack(side=tk.LEFT, padx=5)

        tk.Label(setting_frame, text="   鼠标模式：").pack(side=tk.LEFT)

        self.mode_var = tk.StringVar(value="wall")

        tk.Radiobutton(
            setting_frame,
            text="编辑墙/路",
            variable=self.mode_var,
            value="wall",
            command=self.set_edit_mode
        ).pack(side=tk.LEFT, padx=5)

        tk.Radiobutton(
            setting_frame,
            text="设置起点",
            variable=self.mode_var,
            value="start",
            command=self.set_edit_mode
        ).pack(side=tk.LEFT, padx=5)

        tk.Radiobutton(
            setting_frame,
            text="设置终点",
            variable=self.mode_var,
            value="end",
            command=self.set_edit_mode
        ).pack(side=tk.LEFT, padx=5)

        # 信息栏
        self.info_label = tk.Label(
            self.root,
            text="算法: -- | 路径长度: -- | 访问节点: -- | 运行时间: --",
            font=("微软雅黑", 10),
            fg="blue"
        )
        self.info_label.pack(pady=5)

        # 画布
        self.canvas = tk.Canvas(
            self.root,
            width=self.N * self.cell_size,
            height=self.N * self.cell_size,
            bg="white"
        )
        self.canvas.pack(pady=8)
        self.canvas.bind("<Button-1>", self.on_cell_click)

        # 说明
        self.tip_label = tk.Label(
            self.root,
            text="说明：黑色=墙壁，白色=通道，绿色=起点，红色=终点，蓝色=最终路径，浅蓝色=搜索节点。",
            fg="gray",
            font=("微软雅黑", 9)
        )
        self.tip_label.pack(pady=4)

    def set_algorithm(self):
        self.algorithm = self.algo_var.get()

    def set_animation(self):
        self.animate = self.anim_var.get() == 1

    def set_edit_mode(self):
        self.edit_mode = self.mode_var.get()

    def apply_size(self):
        new_size = int(self.size_var.get())

        if new_size % 2 == 0:
            messagebox.showwarning("提示", "迷宫大小建议使用奇数。")
            return

        self.N = new_size
        self.start = (1, 1)
        self.end = (self.N - 2, self.N - 2)

        # 根据迷宫大小自动调整格子尺寸，避免窗口过大
        if self.N <= 21:
            self.cell_size = 22
        elif self.N <= 31:
            self.cell_size = 16
        else:
            self.cell_size = 12

        self.canvas.config(
            width=self.N * self.cell_size,
            height=self.N * self.cell_size
        )

        self.generate_maze()

    # =========================
    # 二、迷宫生成
    # =========================

    def generate_maze(self):
        self.maze = [[1] * self.N for _ in range(self.N)]

        def carve(x, y):
            self.maze[x][y] = 0
            directions = DIRS.copy()
            random.shuffle(directions)

            for dx, dy in directions:
                nx = x + dx * 2
                ny = y + dy * 2

                if 0 <= nx < self.N and 0 <= ny < self.N and self.maze[nx][ny] == 1:
                    self.maze[x + dx][y + dy] = 0
                    self.maze[nx][ny] = 0
                    carve(nx, ny)

        carve(self.start[0], self.start[1])

        self.maze[self.start[0]][self.start[1]] = 0
        self.maze[self.end[0]][self.end[1]] = 0

        self.clear_search_data()
        self.draw_maze()
        self.reset_info()

    # =========================
    # 三、绘制函数
    # =========================

    def draw_maze(self):
        self.canvas.delete("all")

        for i in range(self.N):
            for j in range(self.N):
                x1 = j * self.cell_size
                y1 = i * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                color = "black" if self.maze[i][j] == 1 else "white"

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline="lightgray"
                )

        self.draw_start_end()

    def draw_start_end(self):
        sx = self.start[1] * self.cell_size
        sy = self.start[0] * self.cell_size

        self.canvas.create_rectangle(
            sx, sy,
            sx + self.cell_size,
            sy + self.cell_size,
            fill="green",
            outline="gray"
        )
        self.canvas.create_text(
            sx + self.cell_size // 2,
            sy + self.cell_size // 2,
            text="起",
            fill="white",
            font=("微软雅黑", max(8, self.cell_size // 2), "bold")
        )

        ex = self.end[1] * self.cell_size
        ey = self.end[0] * self.cell_size

        self.canvas.create_rectangle(
            ex, ey,
            ex + self.cell_size,
            ey + self.cell_size,
            fill="red",
            outline="gray"
        )
        self.canvas.create_text(
            ex + self.cell_size // 2,
            ey + self.cell_size // 2,
            text="终",
            fill="white",
            font=("微软雅黑", max(8, self.cell_size // 2), "bold")
        )

    def draw_visit_cell(self, cell):
        if cell == self.start or cell == self.end:
            return

        i, j = cell
        x1 = j * self.cell_size
        y1 = i * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size

        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="light blue",
            outline="lightgray"
        )

    def draw_path(self):
        for cell in self.path:
            if cell == self.start or cell == self.end:
                continue

            i, j = cell
            x1 = j * self.cell_size
            y1 = i * self.cell_size
            x2 = x1 + self.cell_size
            y2 = y1 + self.cell_size

            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill="deep sky blue",
                outline="gray"
            )

        self.draw_start_end()

    # =========================
    # 四、通用工具
    # =========================

    def clear_search_data(self):
        self.path = []
        self.visited_order = []
        self.last_result = None

    def clear_path(self):
        self.clear_search_data()
        self.draw_maze()
        self.reset_info()

    def reset_info(self):
        self.info_label.config(
            text="算法: -- | 路径长度: -- | 访问节点: -- | 运行时间: --"
        )

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def is_valid_cell(self, x, y):
        return 0 <= x < self.N and 0 <= y < self.N and self.maze[x][y] == 0

    def reconstruct_path(self, parent):
        path = []
        cur = self.end

        while cur != self.start:
            path.append(cur)
            cur = parent[cur]

        path.append(self.start)
        path.reverse()
        return path

    # =========================
    # 五、三种算法
    # =========================

    def solve_maze(self):
        if self.algorithm == "DFS":
            result = self.dfs_search()
        elif self.algorithm == "BFS":
            result = self.bfs_search()
        else:
            result = self.astar_search()

        self.show_result(result)

    def dfs_search(self):
        start_time = time.perf_counter()

        stack = [self.start]
        visited = set()
        parent = {}
        visited_order = []

        visited.add(self.start)
        found = False

        while stack:
            current = stack.pop()
            visited_order.append(current)

            if current == self.end:
                found = True
                break

            x, y = current

            for dx, dy in DIRS:
                nx = x + dx
                ny = y + dy
                next_cell = (nx, ny)

                if self.is_valid_cell(nx, ny) and next_cell not in visited:
                    visited.add(next_cell)
                    parent[next_cell] = current
                    stack.append(next_cell)

        end_time = time.perf_counter()
        path = self.reconstruct_path(parent) if found else []

        return {
            "algorithm": "DFS",
            "found": found,
            "path": path,
            "visited_order": visited_order,
            "visited_count": len(visited_order),
            "path_length": len(path) - 1 if found else 0,
            "runtime": (end_time - start_time) * 1000
        }

    def bfs_search(self):
        start_time = time.perf_counter()

        queue = deque([self.start])
        visited = set()
        parent = {}
        visited_order = []

        visited.add(self.start)
        found = False

        while queue:
            current = queue.popleft()
            visited_order.append(current)

            if current == self.end:
                found = True
                break

            x, y = current

            for dx, dy in DIRS:
                nx = x + dx
                ny = y + dy
                next_cell = (nx, ny)

                if self.is_valid_cell(nx, ny) and next_cell not in visited:
                    visited.add(next_cell)
                    parent[next_cell] = current
                    queue.append(next_cell)

        end_time = time.perf_counter()
        path = self.reconstruct_path(parent) if found else []

        return {
            "algorithm": "BFS",
            "found": found,
            "path": path,
            "visited_order": visited_order,
            "visited_count": len(visited_order),
            "path_length": len(path) - 1 if found else 0,
            "runtime": (end_time - start_time) * 1000
        }

    def astar_search(self):
        start_time = time.perf_counter()

        open_set = []
        heapq.heappush(open_set, (self.heuristic(self.start, self.end), 0, self.start))

        g_score = {self.start: 0}
        parent = {}
        visited = set()
        visited_order = []

        found = False

        while open_set:
            _, current_cost, current = heapq.heappop(open_set)

            if current in visited:
                continue

            visited.add(current)
            visited_order.append(current)

            if current == self.end:
                found = True
                break

            x, y = current

            for dx, dy in DIRS:
                nx = x + dx
                ny = y + dy
                next_cell = (nx, ny)

                if self.is_valid_cell(nx, ny):
                    new_cost = current_cost + 1

                    if next_cell not in g_score or new_cost < g_score[next_cell]:
                        g_score[next_cell] = new_cost
                        parent[next_cell] = current
                        f_score = new_cost + self.heuristic(next_cell, self.end)
                        heapq.heappush(open_set, (f_score, new_cost, next_cell))

        end_time = time.perf_counter()
        path = self.reconstruct_path(parent) if found else []

        return {
            "algorithm": "A*",
            "found": found,
            "path": path,
            "visited_order": visited_order,
            "visited_count": len(visited_order),
            "path_length": len(path) - 1 if found else 0,
            "runtime": (end_time - start_time) * 1000
        }

    # =========================
    # 六、结果显示与动画
    # =========================

    def show_result(self, result):
        self.last_result = result
        self.path = result["path"]
        self.visited_order = result["visited_order"]

        self.draw_maze()

        if not result["found"]:
            self.info_label.config(
                text=f"算法: {result['algorithm']} | 无通路 | "
                     f"访问节点: {result['visited_count']} | "
                     f"运行时间: {result['runtime']:.3f} ms"
            )
            messagebox.showinfo("无解", f"{result['algorithm']} 未找到通路。")
            return

        if self.animate:
            self.anim_index = 0
            self.play_animation()
        else:
            self.draw_path()

        self.info_label.config(
            text=f"算法: {result['algorithm']} | "
                 f"路径长度: {result['path_length']} 步 | "
                 f"访问节点: {result['visited_count']} | "
                 f"运行时间: {result['runtime']:.3f} ms"
        )

    def play_animation(self):
        if self.anim_index < len(self.visited_order):
            cell = self.visited_order[self.anim_index]
            self.draw_visit_cell(cell)
            self.anim_index += 1
            self.root.after(self.anim_delay, self.play_animation)
        else:
            self.draw_path()

    # =========================
    # 七、算法对比与导出
    # =========================

    def compare_algorithms(self):
        results = [
            self.dfs_search(),
            self.bfs_search(),
            self.astar_search()
        ]

        self.last_compare_results = results

        win = tk.Toplevel(self.root)
        win.title("算法性能对比")
        win.geometry("680x300")

        title = tk.Label(
            win,
            text="DFS、BFS、A* 算法性能对比",
            font=("微软雅黑", 14, "bold")
        )
        title.pack(pady=10)

        columns = ("algorithm", "found", "path_length", "visited_count", "runtime")
        tree = ttk.Treeview(win, columns=columns, show="headings", height=6)

        tree.heading("algorithm", text="算法")
        tree.heading("found", text="是否找到")
        tree.heading("path_length", text="路径长度")
        tree.heading("visited_count", text="访问节点数")
        tree.heading("runtime", text="运行时间/ms")

        tree.column("algorithm", width=100, anchor="center")
        tree.column("found", width=100, anchor="center")
        tree.column("path_length", width=120, anchor="center")
        tree.column("visited_count", width=120, anchor="center")
        tree.column("runtime", width=140, anchor="center")

        for result in results:
            tree.insert(
                "",
                tk.END,
                values=(
                    result["algorithm"],
                    "是" if result["found"] else "否",
                    result["path_length"] if result["found"] else "--",
                    result["visited_count"],
                    f"{result['runtime']:.3f}"
                )
            )

        tree.pack(pady=10)

        explain = tk.Label(
            win,
            text="说明：DFS 使用栈，不保证最短；BFS 使用队列，保证最短；A* 使用优先队列和曼哈顿距离，通常访问节点更少。",
            fg="gray",
            font=("微软雅黑", 9)
        )
        explain.pack(pady=5)

    def export_compare_results(self):
        if not self.last_compare_results:
            self.last_compare_results = [
                self.dfs_search(),
                self.bfs_search(),
                self.astar_search()
            ]

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt")]
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["迷宫大小", f"{self.N} x {self.N}"])
                writer.writerow([])
                writer.writerow(["算法", "是否找到", "路径长度", "访问节点数", "运行时间/ms"])

                for result in self.last_compare_results:
                    writer.writerow([
                        result["algorithm"],
                        "是" if result["found"] else "否",
                        result["path_length"] if result["found"] else "--",
                        result["visited_count"],
                        f"{result['runtime']:.3f}"
                    ])

            messagebox.showinfo("导出成功", f"算法对比结果已导出到：\n{file_path}")

        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    # =========================
    # 八、保存与加载迷宫
    # =========================

    def save_maze(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"{self.N}\n")
                f.write(f"{self.start[0]} {self.start[1]}\n")
                f.write(f"{self.end[0]} {self.end[1]}\n")

                for row in self.maze:
                    f.write("".join(str(cell) for cell in row) + "\n")

            messagebox.showinfo("保存成功", f"迷宫已保存到：\n{file_path}")

        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def load_maze(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt")]
        )

        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]

            new_n = int(lines[0])
            start_row, start_col = map(int, lines[1].split())
            end_row, end_col = map(int, lines[2].split())

            maze_lines = lines[3:]

            if len(maze_lines) != new_n:
                raise ValueError("迷宫行数与文件记录的大小不匹配。")

            new_maze = []
            for line in maze_lines:
                if len(line) != new_n:
                    raise ValueError("迷宫列数与文件记录的大小不匹配。")
                new_maze.append([int(ch) for ch in line])

            self.N = new_n
            self.size_var.set(str(new_n))
            self.start = (start_row, start_col)
            self.end = (end_row, end_col)
            self.maze = new_maze

            self.maze[self.start[0]][self.start[1]] = 0
            self.maze[self.end[0]][self.end[1]] = 0

            if self.N <= 21:
                self.cell_size = 25
            elif self.N <= 31:
                self.cell_size = 20
            else:
                self.cell_size = 15

            self.canvas.config(
                width=self.N * self.cell_size,
                height=self.N * self.cell_size
            )

            self.clear_search_data()
            self.draw_maze()
            self.reset_info()

            messagebox.showinfo("加载成功", "迷宫已成功加载。")

        except Exception as e:
            messagebox.showerror("加载失败", str(e))

    # =========================
    # 九、鼠标交互
    # =========================

    def on_cell_click(self, event):
        col = event.x // self.cell_size
        row = event.y // self.cell_size

        if not (0 <= row < self.N and 0 <= col < self.N):
            return

        cell = (row, col)

        if self.edit_mode == "wall":
            if cell == self.start or cell == self.end:
                return

            self.maze[row][col] = 1 - self.maze[row][col]

        elif self.edit_mode == "start":
            if cell == self.end:
                return

            self.start = cell
            self.maze[row][col] = 0

        elif self.edit_mode == "end":
            if cell == self.start:
                return

            self.end = cell
            self.maze[row][col] = 0

        self.clear_search_data()
        self.draw_maze()
        self.reset_info()


if __name__ == "__main__":
    root = tk.Tk()
    app = MazeApp(root)
    root.mainloop()
