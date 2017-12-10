all:
	rm antispam
	chmod +x antispam.py
	ln -s antispam.py antispam

clean:
	rm -rf antispam *.pyc

