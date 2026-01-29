# MDLinks

Generate Markdown links from a bunch of URLs.

By default, uses the page `<title>` as the link text.

Example usage:

```
% cat > urls.txt
https://example.com/
https://en.wikipedia.org/wiki/Example
https://wiki.archlinux.org/title/File_permissions_and_attributes
```

```
% mdlinks < urls.txt
* [Example Domain](https://example.com/)
* [Example - Wikipedia](https://en.wikipedia.org/wiki/Example)
* [File permissions and attributes - ArchWiki](https://wiki.archlinux.org/title/File_permissions_and_attributes)
```
