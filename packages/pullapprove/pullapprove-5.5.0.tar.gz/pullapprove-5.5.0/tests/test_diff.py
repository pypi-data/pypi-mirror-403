from pullapprove.diff import DiffCode, iterate_diff_parts


def test_diff_hunk_context_line():
    # Technically there is a space missing here on the empty line
    diff = """diff --git a/LICENSE b/LICENSE
index fdddb29..314ba5d 100644
--- a/LICENSE
+++ b/LICENSE
@@ -6,7 +6,7 @@ binary, for any purpose, commercial or non-commercial, and by any
 means.

 In jurisdictions that recognize copyright laws, the author or authors
-of this software dedicate any and all copyright interest in the
+of this software dedicate any and all copyright interest! in the
 software to the public domain. We make this dedication for the benefit
 of the public at large and to the detriment of our heirs and
 successors. We intend this dedication to be an overt act of"""

    # Make sure the line with "binary" is seen
    lines = list(iterate_diff_parts(diff))

    # Filter down to the DiffCode objects so we can inspect the actual lines
    code_lines = [line for line in lines if isinstance(line, DiffCode)]

    # We should have parsed the trailing context that appears on the same
    # line as the hunk header ("binary, for any purpose ...")
    assert any(
        "binary, for any purpose" in code_line.content for code_line in code_lines
    ), "The first context line that trails the hunk header was not captured."
