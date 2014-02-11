set -x

zenpack --remove ZenPacks.zenoss.HBase
cd ..
zenpack --link --install .

zopectl restart
zenhub restart

set +x
