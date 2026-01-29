from rich.text import Text

def render_result(
    console,
    boxed,
    title: str,
    result,
    success_message: str | None = None,
):
    if result is None:
        if success_message:
            console.print(
                boxed(title, Text(success_message, style="green"))
            )
        return

    if isinstance(result, str):
        console.print(
            boxed(title, Text(result))
        )
        return

    console.print(
        boxed(title, result)
    )

