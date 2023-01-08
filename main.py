import curses
import enum
import random
import time
from collections import defaultdict
from dataclasses import dataclass


class BallState(enum.Enum):
    IN_PLAY = 0
    STOPPED = 1
    LIMITED = 2


@dataclass
class Ball:
    y: int
    x: int
    symbol: str = "*"

    def update_pos(self, dy, dx):
        self.y += dy
        self.x += dx

    def render(self):
        return self.symbol

    def tick(self, prob, board) -> BallState:
        """Drop a ball and check for collisions"""
        # check for collisions
        if isinstance(board.grid[self.y + 1][self.x], Peg):
            board.remove_ball(self)
            if random.random() < prob:
                self.update_pos(dy=1, dx=-1)
            else:
                self.update_pos(dy=1, dx=1)
            board.add_ball(self)
        elif isinstance(board.grid[self.y + 1][self.x], Ball):
            if self.y == board.top_offset + board.height + 1:
                return BallState.LIMITED
            else:
                return BallState.STOPPED
        else:  # no collision, drop ball
            if self.y < board.top_offset + board.height + board.bottom_offset - 1:
                board.remove_ball(self)
                self.update_pos(dy=1, dx=0)
                board.add_ball(self)
            else:
                return BallState.STOPPED

        return BallState.IN_PLAY


class Peg:
    ...


class GaltonBoard:
    def __init__(
        self,
        height,
        width,
        bottom_offset=0,
        top_offset=0,
        left_offset=1,
        right_offset=1,
    ):
        self.height = height
        self.width = width
        self.bottom_offset = bottom_offset
        self.top_offset = top_offset
        self.left_offset = left_offset
        self.right_offset = right_offset
        self.grid = defaultdict(lambda: defaultdict(lambda: None))
        self.render_dict = defaultdict(lambda: " ")
        self.render_dict.update(
            {
                Ball: "●",
                Peg: ".",
            }
        )
        self.generate_board()

    def generate_board(self):
        for i in range(self.top_offset, self.top_offset + self.height):
            for j in range(self.left_offset, self.width - self.right_offset):
                if i % 2 == 0:  # even rows
                    if j % 2 == 0:  # even columns
                        self.grid[i][j] = Peg()
                else:  # odd rows
                    if j % 2 == 1:  # odd columns
                        self.grid[i][j] = Peg()

    def add_ball(self, ball):
        self.grid[ball.y][ball.x] = ball

    def remove_ball(self, ball):
        self.grid[ball.y][ball.x] = None

    def render_board(self):
        """Render the board"""
        out_lines = []
        for i in range(self.top_offset + self.height + self.bottom_offset):
            line = " " * self.left_offset
            for j in range(self.left_offset, self.width - self.right_offset):
                line += self.render_dict[type(self.grid[i][j])]
            out_lines.append(line)
        return "\n".join(out_lines)


def main(stdscr):
    # general config
    curses.noecho()
    curses.curs_set(0)
    curses.start_color()
    stdscr.nodelay(True)
    BASE_BALL_SPEED = 0.1

    while True:
        # clean up
        stdscr.clear()
        stdscr.refresh()

        # make and render the board
        # inside loop for handling resizing
        # most terminals are much wider than they are tall
        # so board width is based on height
        NUM_ROWS, NUM_COLS = curses.LINES, curses.COLS
        TOP_OFFSET, BOTTOM_OFFSET = 1, NUM_ROWS // 2
        HEIGHT = NUM_ROWS - TOP_OFFSET - BOTTOM_OFFSET
        LEFT_OFFSET, RIGHT_OFFSET = (
            int((NUM_COLS - HEIGHT) / 2.5),
            int((NUM_COLS - HEIGHT) / 2.5)
            + (NUM_COLS % 2 == 0),  # keeps it symmetrical
        )
        board = GaltonBoard(
            HEIGHT,
            NUM_COLS,
            BOTTOM_OFFSET,
            TOP_OFFSET,
            LEFT_OFFSET,
            RIGHT_OFFSET,
        )
        prob = random.uniform(0.3, 0.7)
        board.generate_board()  # reset the board
        stdscr.addstr(0, 0, board.render_board())
        stdscr.refresh()

        # start dropping balls
        balls = []
        add_ball = True
        for ix in range(100_000):
            # check for user input
            try:
                wch = stdscr.get_wch()
            except curses.error:
                pass
            else:
                if wch in ["q", "Q", "\n"]:
                    return

            # add new ball
            if add_ball and ix % 5 == 0:
                ball = Ball(0, curses.COLS // 2)
                board.add_ball(ball)
                balls.append(ball)

            # render and tick
            stdscr.addstr(0, 0, board.render_board())
            stdscr.refresh()
            res = [ball.tick(prob, board) for ball in balls]
            time.sleep(BASE_BALL_SPEED)

            # check if we should stop adding balls
            # check if all balls are stopped
            if any([r == BallState.LIMITED for r in res]):
                add_ball = False
            if all([r in set([BallState.STOPPED, BallState.LIMITED]) for r in res]):
                break

        # time between runs
        time.sleep(2.5)


if __name__ == "__main__":
    curses.wrapper(main)
