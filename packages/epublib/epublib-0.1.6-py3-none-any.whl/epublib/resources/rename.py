from epublib.util import get_absolute_href, get_relative_href, split_fragment


def update_reference_in_same_file(
    old_filename: str,
    new_filename: str,
    reference: str,
    ignore_fragment: bool = False,
) -> str:
    """
    Update a reference within the same file when that file is renamed.

    Args:
        old_filename: The original filename of the file containing the reference.
        new_filename: The new filename of the file after renaming.
        reference: The original reference to be updated.
        ignore_fragment: Whether to ignore the fragment part of the reference.
    """

    ref, identifier = (
        split_fragment(reference) if not ignore_fragment else (reference, None)
    )

    old_absolute_ref = get_absolute_href(
        old_filename,
        ref,
    )

    if not ref:
        return ref

    if old_absolute_ref == old_filename:
        new_ref = get_relative_href(
            new_filename,
            new_filename,
        )
    else:
        new_ref = get_relative_href(
            new_filename,
            old_absolute_ref,
        )

    return new_ref + (f"#{identifier}" if identifier else "")


def update_reference(
    base_filename: str,
    old_filename: str,
    new_filename: str,
    reference: str,
    use_absolute: bool = False,
    ignore_fragment: bool = False,
) -> str | None:
    if use_absolute:
        if old_filename == reference:
            return new_filename
    else:
        ref, identifier = (
            split_fragment(reference) if not ignore_fragment else (reference, None)
        )
        old_absolute_ref = get_absolute_href(
            base_filename,
            ref,
        )

        if old_absolute_ref == old_filename:
            new_ref = get_relative_href(
                base_filename,
                new_filename,
            )
            return new_ref + (f"#{identifier}" if identifier else "")
