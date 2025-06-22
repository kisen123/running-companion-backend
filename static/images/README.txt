To compress the images, have ImageMagick installed, and perform this in PowerShell inside the static/images folder:

Get-ChildItem -Recurse -Filter *.jpg | ForEach-Object {
    $newName = $_.DirectoryName + "\" + $_.BaseName + "_compressed.jpg"
    magick $_.FullName -resize 1024x1024 -quality 70 $newName
}

Get-ChildItem -Recurse -Filter *_compressed.jpg | ForEach-Object {
    $original = $_.DirectoryName + "\" + $_.BaseName.Replace("_compressed", "") + ".jpg"
    Move-Item $_.FullName $original -Force
}