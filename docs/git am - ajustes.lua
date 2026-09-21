git am --abort                              # ou se já fez abort:
Remove-Item -Recurse -Force .git\rebase-apply
git restore <arquivo_conflitante>           # restaura ao HEAD
git apply --ignore-space-change --whitespace=fix 0001-*.patch