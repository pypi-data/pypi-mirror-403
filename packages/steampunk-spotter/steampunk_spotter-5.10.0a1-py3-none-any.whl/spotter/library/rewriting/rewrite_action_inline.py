"""RewriteActionInline implementation."""

import re
from typing import Optional, Tuple

from spotter.library.rewriting.models import Replacement, RewriteBase, RewriteSuggestion
from spotter.library.rewriting.rewrite_module_inline import RewriteModuleInline


class RewriteActionInline(RewriteBase):
    """RewriteActionInline implementation."""

    def get_regex(self, text_before: str) -> str:
        return rf"^(\s*({text_before}\s*):)"

    def remove_module_name(self, content: str, suggestion: RewriteSuggestion) -> Tuple[str, RewriteSuggestion]:
        """
        Remove module name from content.

        :param content: Content that we want to rewrite
        :param suggestion: Suggestion object
        """
        module_replacement = RewriteModuleInline(suggestion).get_replacement(content, suggestion)
        if module_replacement is None:
            module_name = suggestion.suggestion_spec["data"]["module_name"]
            print(f'Applying suggestion failed: could not find "{module_name}" to replace.')
            raise TypeError()
        rewrite_result = module_replacement.apply()
        suggestion.end_mark += rewrite_result.diff_size
        return rewrite_result.content, suggestion

    def get_replacement(self, content: str, suggestion: RewriteSuggestion) -> Optional[Replacement]:
        suggestion_data = suggestion.suggestion_spec["data"]
        suggestion_clone = suggestion.clone()
        content, suggestion_clone = self.remove_module_name(content, suggestion_clone)
        part = self.get_context(content, suggestion_clone)

        before = suggestion_data["original_module_name"]
        regex = self.get_regex(before)
        match = re.search(regex, part, re.MULTILINE)
        after = suggestion_data["module_name"]
        if match is None:
            print(
                f"Applying suggestion {suggestion_clone.suggestion_spec} failed at "
                f"{suggestion_clone.file}:{suggestion_clone.line}:{suggestion_clone.column}: could not find string to replace."
            )
            return None
        replacement = Replacement(content, suggestion_clone, match, after)
        return replacement
