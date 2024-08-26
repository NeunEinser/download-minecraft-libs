import os
import platform
import requests
import sys

VERSION_MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"

def main():
	if len(sys.argv) < 2 or len(sys.argv) > 3:
		print(f"Syntax: {sys.argv[0]} <minecraft version> [os]", file=sys.stderr)
		return -1
	
	manifest = requests.get(VERSION_MANIFEST_URL).json()
	versions: list[dict] = manifest["versions"]

	version: dict | None = None
	for v in versions:
		if v["id"] == sys.argv[1]:
			version = v
			break

	if version == None:
		print(f"Minecraft version {sys.argv[1]} not found", file=sys.stderr)
		return -1

	version_data = requests.get(version["url"]).json()
	libs: list[dict] = version_data["libraries"]
	op_sys = None
	if len(sys.argv) == 3:
		op_sys = sys.argv[2]
	else:
		op_sys = platform.system().lower()
		if op_sys == "darwin":
			op_sys = "osx"
	if op_sys not in ["linux", "windows", "osx"]:
		print(f"Unsupported OS {op_sys}, should be one of \"linux\", \"windows\" or \"osx\"", file=sys.stderr)
		return -1
	
	if os.path.exists(f"out/{sys.argv[1]}"):
		print(f"{sys.argv[1]} already exists", file=sys.stderr)
		return -1

	for lib in libs:
		downloads: dict = lib["downloads"]
		artifact: dict = downloads["artifact"]
		rules: list[dict] | None = lib.get("rules")
		action = "allow"
		if rules != None:
			action = "disallow"
			for rule in rules:
				rule_os: dict | None = rule.get("os")
				if rule_os == None or rule_os["name"] == op_sys:
					action: str = rule["action"]

		if action == "allow":
			path=f"out/{sys.argv[1]}/{artifact['path']}"
			print(f"Downloading {path}")
			os.makedirs(path[0:path.rindex('/')], exist_ok=True)
			lib_bin = requests.get(artifact["url"]).content

			if not os.path.exists(path):
				with open(path, "xb") as file:
					file.write(lib_bin)
			
			natives: dict[str, str] | None = lib.get("natives")
			natives_key = None
			if natives != None:
				natives_key = natives.get(op_sys)
			
			if natives_key != None:
				natives_download: dict = downloads["classifiers"][natives_key]

				natives_path=f"out/{sys.argv[1]}/{natives_download['path']}"
				print(f"Downloading {natives_path}")
				os.makedirs(natives_path[0:natives_path.rindex('/')], exist_ok=True)
				natives_bin = requests.get(natives_download["url"]).content


				if not os.path.exists(natives_path):
					with open(natives_path, "xb") as file:
						file.write(natives_bin)


if __name__ == "__main__":
	main()
