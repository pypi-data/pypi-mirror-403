import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
from .core import JeomMaeChu

from typing import Optional

app = typer.Typer(
    help="운명에 맡기는 점심 메뉴 추천기! - 'jeomaechu'만 입력하면 즉시 추천!",
    rich_markup_mode="rich",
    no_args_is_help=False
)
console = Console()
engine = JeomMaeChu()

# Sorthand mapping for categories
CAT_MAP = {
    "한": "Korean (한식)",
    "집": "Real Home (찐 집밥/현실)",
    "일": "Japanese (일본어/일식)",
    "중": "Chinese (중국어/중식)",
    "양": "Western (양식)",
    "아": "Asian (아시아/기타)",
    "상": "Brand (프랜차이즈/매장)"
}

def _perform_pick(categories: Optional[List[str]] = None, tags: Optional[List[str]] = None, count: int = 1):
    """Internal helper to avoid Typer OptionInfo issues during direct calls."""
    # Resolve category shorthands
    if categories:
        categories = [CAT_MAP.get(c, c) for c in categories]
        
    console.print("[bold cyan]점심 메뉴를 추천해드립니다![/bold cyan]\n")
    
    if count > 1 or (categories and len(categories) > 0) or (tags and len(tags) > 0):
        results = engine.recommend_many(count, categories=categories, tags=tags)
        if not results:
            rprint(f"[red]해당 조건에 맞는 메뉴가 없습니다.[/red]")
            return
        
        table = Table(title=f"추천 메뉴 ({len(results)}가지)")
        table.add_column("No.", justify="right", style="dim")
        table.add_column("카테고리", style="yellow")
        table.add_column("메뉴명", style="bold green")
        
        for i, (cat, menu) in enumerate(results, 1):
            table.add_row(str(i), cat or "Tag Pick", menu)
        
        console.print(table)
        return

    result_text = ""
    if category:
        menu = engine.recommend_by_category(category)
        if menu:
            result_text = f"[yellow]{category}[/yellow] 중에서 [bold green]'{menu}'[/bold green] 어떠세요?"
        else:
            rprint(f"[red]존재하지 않는 카테고리입니다: {category}[/red]")
            return
    elif tag:
        menu = engine.recommend_by_tag(tag)
        if menu:
            result_text = f"[yellow]{tag}[/yellow] 느낌으로 [bold green]'{menu}'[/bold green] 어떠세요?"
        else:
            rprint(f"[red]존재하지 않는 태그입니다: {tag}[/red]")
            return
    else:
        cat, menu = engine.recommend_random()
        result_text = f"[yellow]{cat}[/yellow] 카테고리의 [bold green]'{menu}'[/bold green] 어떠세요?"

    console.print(Panel(result_text, title="추천 메뉴", expand=False))

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    category: Optional[List[str]] = typer.Option(None, "--category", "-c", help="카테고리 선택 (여러 번 사용 가능)"),
    tag: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="태그 선택 (여러 번 사용 가능)"),
    count: int = typer.Option(1, "--count", "-n", help="개수 선택")
):
    """점메추(Jeom-Mae-Chu) - 오늘의 점심 메뉴를 정해드립니다."""
    if ctx.invoked_subcommand is None:
        _perform_pick(category, tag, count)

@app.command(name="pick", help="[bold yellow]메뉴 추천 받기 (기본 명령어)[/bold yellow]")
def pick(
    category: Optional[List[str]] = typer.Option(None, "--category", "-c", help="카테고리 선택"),
    tag: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="태그 선택"),
    count: int = typer.Option(1, "--count", "-n", help="개수 선택")
):
    """Pick random lunch menus for today!"""
    _perform_pick(category, tag, count)

# Alias commands
@app.command(name="p", hidden=True)
def pick_alias(
    category: Optional[List[str]] = typer.Option(None, "--category", "-c", help="카테고리 선택"),
    tag: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="태그 선택"),
    count: int = typer.Option(1, "--count", "-n", help="개수 선택")
):
    _perform_pick(category, tag, count)

@app.command(name="cats", help="카테고리 목록 보기")
def list_categories():
    """List all available menu categories."""
    table = Table(title="Menu Categories")
    table.add_column("Category Name", style="cyan")
    for cat in engine.get_categories():
        table.add_row(cat)
    console.print(table)

@app.command(name="c", hidden=True)
def cats_alias():
    list_categories()

@app.command(name="tags", help="태그 목록 보기")
def list_tags():
    """List all available tags/moods."""
    table = Table(title="Menu Tags")
    table.add_column("Tag Name", style="magenta")
    for tag in engine.get_tags():
        table.add_row(tag)
    console.print(table)

@app.command(name="t", hidden=True)
def tags_alias():
    list_tags()

@app.command(name="all", help="[cyan]전체 메뉴 데이터베이스 확인[/cyan]")
def show_all():
    """Show ALL available menus in the database, grouped by category."""
    console.print("[bold green]전체 메뉴 데이터베이스[/bold green]\n")
    
    for category, menus in engine.menus.items():
        table = Table(title=f"[bold yellow]{category}[/bold yellow]", show_header=False, box=None)
        table.add_column("메뉴", style="cyan")
        
        # Display in rows of 6
        cols = 6
        for i in range(0, len(menus), cols):
            row_items = menus[i:i + cols]
            table.add_row(", ".join(row_items))
        
        console.print(table)
        console.print("-" * 40)

@app.command(name="a", hidden=True)
def all_alias():
    show_all()

# --- Pro Shorthand Commands (Direct Korean) ---

@app.command(name="대충", help="귀찮을 때 초간단 메뉴 추천")
def quick_korean(count: int = 1):
    _perform_pick(tags=["Quick (간편한/초간단)"], count=count)

@app.command(name="집밥", help="현실적인 집밥 메뉴 추천")
def home_korean(count: int = 1):
    _perform_pick(categories=["Real Home (찐 집밥/현실)"], count=count)

@app.command(name="자취", help="자취생을 위한 메뉴 추천")
def bachelor_korean(count: int = 1):
    _perform_pick(categories=["Real Home (찐 집밥/현실)"], count=count)

@app.command(name="자취생", hidden=True)
def bachelor_alias(count: int = 1):
    _perform_pick(categories=["Real Home (찐 집밥/현실)"], count=count)

@app.command(name="혼밥", help="혼자 먹기 좋은 메뉴")
def solo_korean(count: int = 1):
    _perform_pick(categories=["Real Home (찐 집밥/현실)"], count=count)

@app.command(name="자취요리", hidden=True)
def solo_alias(count: int = 1):
    _perform_pick(categories=["Real Home (찐 집밥/현실)"], count=count)

@app.command(name="분식", help="떡볶이, 김밥 등 분식 추천")
def snack_direct(count: int = 1):
    _perform_pick(tags=["Snack (분식)"], count=count)

@app.command(name="술안주", help="안주로도 좋은 메뉴")
def bar_direct(count: int = 1):
    _perform_pick(tags=["Bar Food (술안주)"], count=count)

@app.command(name="안주", hidden=True)
def bar_alias(count: int = 1):
    _perform_pick(tags=["Bar Food (술안주)"], count=count)

@app.command(name="한식", help="바로 한식 추천")
def korean_direct(count: int = 1):
    _perform_pick(categories=["Korean (한식)"], count=count)

@app.command(name="중식", help="바로 중식 추천")
def chinese_direct(count: int = 1):
    _perform_pick(categories=["Chinese (중국어/중식)"], count=count)

@app.command(name="일식", help="바로 일식 추천")
def japanese_direct(count: int = 1):
    _perform_pick(categories=["Japanese (일본어/일식)"], count=count)

@app.command(name="아시아", help="아시아 요리 (베트남, 태국, 인도 등)")
def asian_direct(count: int = 1):
    _perform_pick(categories=["Asian (아시아/기타)"], count=count)

@app.command(name="동남아", hidden=True)
def asian_alias1(count: int = 1):
    _perform_pick(categories=["Asian (아시아/기타)"], count=count)

@app.command(name="기타", hidden=True)
def asian_alias2(count: int = 1):
    _perform_pick(categories=["Asian (아시아/기타)"], count=count)

@app.command(name="양식", help="바로 양식 추천")
def western_direct(count: int = 1):
    _perform_pick(categories=["Western (양식)"], count=count)

@app.command(name="고기", help="무조건 고기!")
def meat_direct(count: int = 1):
    _perform_pick(tags=["Meat (고기)"], count=count)

@app.command(name="해물", help="해산물/생선 요리")
def seafood_direct(count: int = 1):
    _perform_pick(tags=["Seafood (해산물)"], count=count)

@app.command(name="매운거", help="스트레스 풀리는 매운 음식")
def spicy_direct(count: int = 1):
    _perform_pick(tags=["Spicy (매콤)"], count=count)

@app.command(name="매워", hidden=True)
def spicy_alias(count: int = 1):
    _perform_pick(tags=["Spicy (매콤)"], count=count)

@app.command(name="국물", help="뜨끈한 국물 요리")
def soupy_direct(count: int = 1):
    _perform_pick(tags=["Soupy (국물/수프)"], count=count)

@app.command(name="해장", help="어제 술 마셨다면? 해장 메뉴")
def hangover_direct(count: int = 1):
    _perform_pick(tags=["Soupy (국물/수프)"], count=count)

@app.command(name="면", help="호로록 면 요리")
def noodle_direct(count: int = 1):
    _perform_pick(tags=["Noodle (면)"], count=count)

@app.command(name="밥", help="역시 한국인은 밥!")
def rice_direct(count: int = 1):
    _perform_pick(tags=["Rice (밥)"], count=count)

@app.command(name="건강", help="가볍고 건강한 식사")
def healthy_direct(count: int = 1):
    _perform_pick(tags=["Healthy (건강식)"], count=count)

@app.command(name="다이어트", hidden=True)
def diet_alias(count: int = 1):
    _perform_pick(tags=["Healthy (건강식)"], count=count)

@app.command(name="헤비", help="오늘은 기름지고 든든하게!")
def heavy_direct(count: int = 1):
    _perform_pick(tags=["Heavy (든든/헤비)"], count=count)

@app.command(name="기름진거", hidden=True)
def oily_alias(count: int = 1):
    _perform_pick(tags=["Heavy (든든/헤비)"], count=count)

@app.command(name="글로벌", help="전 세계 다양한 요리")
def global_direct(count: int = 1):
    _perform_pick(tags=["Global (글로벌)"], count=count)

@app.command(name="세계", hidden=True)
def global_alias(count: int = 1):
    _perform_pick(tags=["Global (글로벌)"], count=count)

@app.command(name="전통", help="전통/원어 느낌의 정통 요리")
def authentic_direct(count: int = 1):
    _perform_pick(tags=["Authentic (전통/원어)"], count=count)

@app.command(name="정통", hidden=True)
def authentic_alias(count: int = 1):
    _perform_pick(tags=["Authentic (전통/원어)"], count=count)

@app.command(name="일상", help="매일 먹어도 좋은 일상 메뉴")
def daily_direct(count: int = 1):
    _perform_pick(tags=["Daily (일상)"], count=count)

@app.command(name="맨날", hidden=True)
def daily_alias(count: int = 1):
    _perform_pick(tags=["Daily (일상)"], count=count)

@app.command(name="브랜드", help="유명 프랜차이즈 메뉴")
def brand_direct(count: int = 1):
    _perform_pick(categories=["Brand (프랜차이즈/매장)"], count=count)

@app.command(name="프차", hidden=True)
def franchise_alias(count: int = 1):
    _perform_pick(categories=["Brand (프랜차이즈/매장)"], count=count)

@app.command(name="아무거나", help="진짜 아무거나 추천해줘!")
def anything_direct(count: int = 1):
    _perform_pick(count=count)

if __name__ == "__main__":
    app()
