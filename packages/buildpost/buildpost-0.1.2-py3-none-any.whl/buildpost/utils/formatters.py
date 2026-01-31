"""Platform-specific post formatters."""

import re
from typing import List, Dict


class PostFormatter:
    """Format posts for different social media platforms."""

    @staticmethod
    def format_for_twitter(
        content: str,
        hashtags: List[str] = None,
        max_length: int = 280
    ) -> str:
        """
        Format post for Twitter/X.

        Args:
            content: Post content
            hashtags: List of hashtags to add
            max_length: Maximum character length

        Returns:
            Formatted post
        """
        # Add hashtags if provided
        if hashtags:
            # Filter to max 3 hashtags
            hashtags = hashtags[:3]
            hashtag_str = ' '.join(hashtags)
            content = f"{content}\n\n{hashtag_str}"

        # Truncate if too long
        if len(content) > max_length:
            # Try to truncate at sentence or word boundary
            content = PostFormatter._smart_truncate(content, max_length)

        return content

    @staticmethod
    def format_for_linkedin(
        content: str,
        hashtags: List[str] = None,
        max_length: int = 3000
    ) -> str:
        """
        Format post for LinkedIn.

        Args:
            content: Post content
            hashtags: List of hashtags to add
            max_length: Maximum character length

        Returns:
            Formatted post
        """
        # LinkedIn prefers hashtags at the end
        if hashtags:
            # Use up to 5 hashtags for LinkedIn
            hashtags = hashtags[:5]
            hashtag_str = ' '.join(hashtags)
            content = f"{content}\n\n{hashtag_str}"

        # Ensure proper paragraph spacing
        content = PostFormatter._ensure_paragraph_spacing(content)

        # Truncate if too long
        if len(content) > max_length:
            content = PostFormatter._smart_truncate(content, max_length)

        return content

    @staticmethod
    def format_for_devto(
        content: str,
        hashtags: List[str] = None,
        max_length: int = 1000
    ) -> str:
        """
        Format post for Dev.to or Hashnode.

        Args:
            content: Post content
            hashtags: List of hashtags to add
            max_length: Maximum character length

        Returns:
            Formatted post
        """
        # Dev.to uses lowercase hashtags without #
        if hashtags:
            # Remove # from hashtags and convert to lowercase
            clean_tags = [tag.lstrip('#').lower() for tag in hashtags]
            hashtag_str = ' '.join([f"#{tag}" for tag in clean_tags])
            content = f"{content}\n\n{hashtag_str}"

        # Truncate if too long
        if len(content) > max_length:
            content = PostFormatter._smart_truncate(content, max_length)

        return content

    @staticmethod
    def format_generic(
        content: str,
        hashtags: List[str] = None,
        max_length: int = 500
    ) -> str:
        """
        Format post for generic platform.

        Args:
            content: Post content
            hashtags: List of hashtags to add
            max_length: Maximum character length

        Returns:
            Formatted post
        """
        if hashtags:
            hashtag_str = ' '.join(hashtags[:3])
            content = f"{content}\n\n{hashtag_str}"

        if len(content) > max_length:
            content = PostFormatter._smart_truncate(content, max_length)

        return content

    @staticmethod
    def _smart_truncate(text: str, max_length: int) -> str:
        """
        Truncate text intelligently at sentence or word boundary.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        # Try to truncate at sentence boundary
        truncated = text[:max_length - 3]

        # Look for last period, exclamation, or question mark
        sentence_endings = ['. ', '! ', '? ']
        last_sentence_end = -1

        for ending in sentence_endings:
            pos = truncated.rfind(ending)
            if pos > last_sentence_end:
                last_sentence_end = pos

        if last_sentence_end > max_length * 0.7:  # At least 70% of max length
            return truncated[:last_sentence_end + 1].rstrip()

        # Otherwise truncate at word boundary
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return truncated[:last_space] + '...'

        # Last resort: hard truncate
        return truncated + '...'

    @staticmethod
    def _ensure_paragraph_spacing(text: str) -> str:
        """
        Ensure proper paragraph spacing (double newline).

        Args:
            text: Text to format

        Returns:
            Text with proper spacing
        """
        # Replace single newlines with double newlines for paragraphs
        # But don't add extra spacing if it's already there
        text = re.sub(r'\n{3,}', '\n\n', text)  # Remove excessive newlines
        return text

    @staticmethod
    def add_hashtags(content: str, hashtags: List[str]) -> str:
        """
        Add hashtags to content.

        Args:
            content: Post content
            hashtags: List of hashtags

        Returns:
            Content with hashtags
        """
        if not hashtags:
            return content

        # Ensure hashtags have #
        formatted_hashtags = [
            tag if tag.startswith('#') else f'#{tag}'
            for tag in hashtags
        ]

        hashtag_str = ' '.join(formatted_hashtags)
        return f"{content}\n\n{hashtag_str}"

    @staticmethod
    def remove_emojis(text: str) -> str:
        """
        Remove emojis from text (useful for LinkedIn professional posts).

        Args:
            text: Text containing emojis

        Returns:
            Text without emojis
        """
        # Remove emojis using regex
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub('', text)

    @staticmethod
    def count_characters(text: str) -> int:
        """
        Count characters in text.

        Args:
            text: Text to count

        Returns:
            Character count
        """
        return len(text)

    @staticmethod
    def validate_length(text: str, max_length: int) -> bool:
        """
        Check if text is within length limit.

        Args:
            text: Text to check
            max_length: Maximum allowed length

        Returns:
            True if within limit
        """
        return len(text) <= max_length


def format_post(
    content: str,
    platform: str,
    platform_config: Dict,
    hashtags: List[str] = None
) -> str:
    """
    Format post for a specific platform.

    Args:
        content: Post content
        platform: Platform name
        platform_config: Platform configuration dict
        hashtags: Optional hashtags to add

    Returns:
        Formatted post
    """
    max_length = platform_config.get('max_length', 500)

    formatters = {
        'twitter': PostFormatter.format_for_twitter,
        'linkedin': PostFormatter.format_for_linkedin,
        'devto': PostFormatter.format_for_devto,
        'generic': PostFormatter.format_generic,
    }

    formatter = formatters.get(platform, PostFormatter.format_generic)
    return formatter(content, hashtags, max_length)
