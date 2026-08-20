import json
import urllib.parse
import urllib.request


class Translator:

    def __init__(
        self,
        source_language="en",
        target_language="fa"
    ):
        self.source_language = source_language
        self.target_language = target_language

    def translate(self, text):

        if not text or not text.strip():
            raise ValueError(
                "Text to translate is empty."
            )

        text = text.strip()

        encoded_text = urllib.parse.quote(text)

        url = (
            "https://translate.googleapis.com/"
            "translate_a/single"
            "?client=gtx"
            "&sl="
            + urllib.parse.quote(
                self.source_language
            )
            + "&tl="
            + urllib.parse.quote(
                self.target_language
            )
            + "&dt=t"
            "&q="
            + encoded_text
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent":
                "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:

            data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

        if not data or not data[0]:
            raise RuntimeError(
                "Translation returned no result."
            )

        translated_parts = []

        for item in data[0]:

            if item and len(item) > 0:

                translated = item[0]

                if translated:
                    translated_parts.append(
                        translated
                    )

        result = "".join(
            translated_parts
        ).strip()

        if not result:
            raise RuntimeError(
                "Translation result is empty."
            )

        return result

    def translate_lines(
        self,
        text,
        callback=None
    ):

        if not text or not text.strip():
            raise ValueError(
                "Text to translate is empty."
            )

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        results = []

        total = len(lines)

        for index, line in enumerate(lines):

            if callback:

                callback(
                    "Translating "
                    + str(index + 1)
                    + "/"
                    + str(total)
                    + "..."
                )

            translated = self.translate(
                line
            )

            results.append(
                translated
            )

        return "\n".join(
            results
      )
