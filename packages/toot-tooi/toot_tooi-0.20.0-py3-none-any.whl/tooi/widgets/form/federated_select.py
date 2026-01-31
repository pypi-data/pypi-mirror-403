from tooi.widgets.form.select import Select


class FederatedSelect(Select[bool]):
    def __init__(
        self,
        value: bool,
        compact: bool = False,
        disabled: bool = False,
    ):
        choices = [
            ("Federated", True),
            ("Not Federated (local only)", False)
        ]

        super().__init__(
            choices,
            prompt="Federation",
            value=value,
            compact=compact,
            disabled=disabled,
            allow_blank=False,
        )
