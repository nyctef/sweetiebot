if [ -z "$1" ]
  then
    echo "No version supplied"
    exit
fi

echo $1 > ../version.txt
git commit -am "bump version"