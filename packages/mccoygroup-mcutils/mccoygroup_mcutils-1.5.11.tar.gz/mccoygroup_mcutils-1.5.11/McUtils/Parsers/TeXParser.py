import re

from . import FileStreamer as Parsers

__all__ = [
    "TeXParser"
]

class TeXParser(Parsers.FileStreamReader):
    @classmethod
    def is_valid_tex_block(cls, block:str):
        block = block.replace("\\{", "|").replace("\\}", "|")
        return block.count("{") == block.count("}") - 1
    @classmethod
    def is_valid_stream_start(cls, tag_str):
        body = tag_str[1:-1]
        return (
            len(body) > 0
            and body.count("[") == body.count("]")
        )
    @classmethod
    def _call_match_test(cls, options):
        if not isinstance(options, str):
            options = "|".join(options)
        options = re.compile(options)
        def matches(tag:str):
            if not cls.is_valid_stream_start(tag):
                return Parsers.FileStreamReader.TagSentinels.Continue
            base = tag[1:].strip("{").partition("[")[0]
            if re.fullmatch(options, base):
                return True
            else:
                return Parsers.FileStreamReader.TagSentinels.NextMatch
        return matches
    def parse_tex_call(self, allowed_calls=None, return_end_points=False):
        if allowed_calls is None:
            tag_validator = self.is_valid_stream_start
            start_tags = "\\"
        else:
            tag_validator = self._call_match_test(allowed_calls)
            if isinstance(allowed_calls, str):
                start_tags = "\\"+allowed_calls
            else:
                start_tags = tuple("\\"+a for a in allowed_calls)
        block = self.parse_key_block(
            tag_start=Parsers.FileStreamerTag(start_tags, follow_ups="{", skip_tag=True),
            tag_end="}",
            validator=self.is_valid_tex_block,
            tag_validator=tag_validator,
            expand_until_valid=True,
            preserve_tag=True,
            allow_terminal=True,
            return_end_points=return_end_points
        )
        more_calls = True
        while more_calls:
            with Parsers.FileStreamCheckPoint(self):
                cur = self.stream.read(1)
            if cur == "{":
                subblock = self.parse_key_block(
                    tag_start=Parsers.FileStreamerTag("{", skip_tag=True),
                    tag_end="}",
                    validator=self.is_valid_tex_block,
                    tag_validator=tag_validator,
                    expand_until_valid=True,
                    preserve_tag=True,
                    allow_terminal=True,
                    return_end_points=return_end_points
                )
                if subblock is not None:
                    if return_end_points:
                        (s0, _), b0 = block
                        (_, e1), sb1 = subblock
                        block = (s0, e1), b0 + sb1
                    else:
                        block = block + subblock
                else:
                    more_calls = False
            else:
                more_calls = False

        return block


    @classmethod
    def _call_body_match_test(cls, calls, options):
        if not isinstance(options, str):
            options = "|".join(options)
        options = re.compile(options)
        base_test = cls._call_match_test(calls)
        def matches(tag: str):
            init_test = base_test(tag)
            if init_test is True:
                base = tag.partition("{")[2][:-1]
                if re.fullmatch(options, base):
                    return True
                else:
                    return Parsers.FileStreamReader.TagSentinels.NextMatch
            else:
                return init_test
        return matches
    @classmethod
    def _valid_environment_test(cls, block:str):
        block = block.replace("\\{", "|").replace("\\}", "|")
        if block.count("{") != block.count("}"):
            return False
        begin_env, _, rest = block.partition("{")[-1].partition("}")
        body, _, end_env = rest.rpartition("{")
        begin_env = begin_env.strip()
        end_env = end_env.strip()
        if begin_env != end_env[:-1]:
            return False
        else:
            return body.count("\\begin{"+begin_env+"}") == body.count("\\end{"+begin_env+"}")
    def parse_tex_environment(self, allowed_environments=None, return_end_points=False):
        if allowed_environments is None:
            tag_validator = self._call_match_test("begin")
            validator = self._valid_environment_test
            tag_start = Parsers.FileStreamerTag("\\begin{", follow_ups=("}",), skip_tag=False)
            tag_end = Parsers.FileStreamerTag("\\end{", follow_ups=("}",), skip_tag=True)
        else:
            tag_validator = self._call_body_match_test("begin", allowed_environments)
            validator = self._valid_environment_test
            if isinstance(allowed_environments, str):
                tag_start = Parsers.FileStreamerTag("\\begin{"+allowed_environments+"}", skip_tag=False)
                tag_end = Parsers.FileStreamerTag("\\end{"+allowed_environments+"}", skip_tag=True)
            else:
                tag_start = Parsers.FileStreamerTag(tuple("\\begin{"+a+"}" for a in allowed_environments), skip_tag=False)
                tag_end = Parsers.FileStreamerTag(tuple("\\end{"+a+"}" for a in allowed_environments), skip_tag=True)

        block = self.parse_key_block(
            tag_start=tag_start,
            tag_end=tag_end,
            validator=validator,
            tag_validator=tag_validator,
            expand_until_valid=True,
            preserve_tag=True,
            allow_terminal=True,
            return_end_points=return_end_points
        )
        if return_end_points:
            eps, body = block
            block = (eps[0], body)

        return block