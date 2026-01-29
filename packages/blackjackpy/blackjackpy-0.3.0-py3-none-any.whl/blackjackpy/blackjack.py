"""ブラックジャックのゲーム"""

# ruff: noqa: T201
import secrets
import typing

POINT21: typing.Final[int] = 21


class Card:
    """**クラス** | カード"""

    def __init__(self, num: int) -> None:
        """カードの初期化

        :param num: 0-52の数字
        """
        self.suit = num // 13 + 1
        self.rank = num % 13 + 1

    def point(self) -> int:
        """カードの得点"""
        return min(10, self.rank)

    def __str__(self) -> str:
        """文字列化"""
        n = self.rank * 2
        m = n - 2
        r = " A 2 3 4 5 6 7 8 910 J Q K"[m:n]
        s = "(" + "DHSC"[self.suit - 1] + ")"
        return r + s


class Owner:
    """**クラス** | 手札を持ち、カードを引ける人"""

    def __init__(self) -> None:
        self.hands = []

    def draw(self, gm: GameMaster) -> None:
        """カードを引く"""
        self.hands.append(gm.pop())

    def sequence(self, *, hidden: bool = False) -> str:
        """手札の文字列化"""
        s = "".join(str(cd) for cd in self.hands)
        return (s[:5] + " *(*)" + s[10:]) if hidden else s

    def point(self) -> int:
        """手札の合計得点"""
        pnt = sum(cd.point() for cd in self.hands)
        for cd in self.hands:
            if cd.rank == 1 and pnt + 10 <= POINT21:
                pnt += 10
        return pnt


class Player(Owner):
    """**クラス** | プレイヤー"""

    @classmethod
    def ask(cls) -> str:
        """標準入力から選択を取得し戻り値とする"""
        print("Hit? (y/n) ", end="")
        return input()

    def act(self, gm: GameMaster) -> None:
        """プレイヤーの手番の処理"""
        while self.point() < POINT21:
            gm.show(hidden=True)
            answer = ""
            while answer not in {"y", "n"}:
                answer = self.ask()
            if answer == "n":
                break
            self.draw(gm)


class Dealer(Owner):
    """**クラス** | ディーラー"""

    LOWER: typing.Final[int] = 17

    def act(self, gm: GameMaster) -> None:
        """ディーラーの手番の処理"""
        while self.point() < self.LOWER:
            self.draw(gm)


class GameMaster:
    """**クラス** | ゲームマスター"""

    def __init__(self, *, cards: list[int] | None = None) -> None:
        """ゲームマスターの初期化

        :param cards: 配布カードのリスト, defaults to None
        """
        if cards:
            self.cards = [Card(i) for i in cards]
        else:
            self.cards = [Card(i) for i in range(52)]
            secrets.SystemRandom().shuffle(self.cards)
        self.player = Player()
        self.dealer = Dealer()

    def start_game(self) -> None:
        """ゲームの開始"""
        for _ in range(2):
            self.player.draw(self)
            self.dealer.draw(self)
        self.player.act(self)
        player_point = self.player.point()
        self.message = "You lose."
        if player_point <= POINT21:
            self.dealer.act(self)
            dealer_point = self.dealer.point()
            if player_point == dealer_point:
                self.message = "Draw."
            elif dealer_point > POINT21 or dealer_point < player_point:
                self.message = "You win."
        self.show(hidden=False)
        print(self.message)

    def show(self, *, hidden: bool) -> None:
        """プレイヤーとディーラーのカード表示

        :param hidden: ディーラーの2枚目を隠すかどうか
        """
        player_point = self.player.point()
        player_sequence = self.player.sequence()
        print(f"Player({player_point:2}): {player_sequence}")
        dealer_point = "--" if hidden else self.dealer.point()
        dealer_sequence = self.dealer.sequence(hidden=hidden)
        print(f"Dealer({dealer_point:2}): {dealer_sequence}")

    def pop(self) -> Card:
        """カードを配る"""
        return self.cards.pop(0)


def main() -> None:
    """ゲーム実行"""
    GameMaster().start_game()
