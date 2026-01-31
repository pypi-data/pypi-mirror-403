"""命令字典定义模块"""

python_pkgs = {
    "uv tool install -U dlght": "免代理 gitub下载工具 dlght",
    "uv tool install -U envvm": "环境变量管理工具 envvm",
    "uv tool install -U ali-ops": "aliyun命令行工具ali-ops",
    # "uv tool install -U iamt": "自动化运维工具iamt #直接报错不能自己操作自己",
    "uv tool install -U cpdts": "脚手架 cpdts",
    "uv tool install -U tschm": "windows定时任务工具",
    "uv tool install -U fastdjt": "django项目脚手架",
    "uv tool install -U ptlearn": "ptlearn",
    "uv tool install -U ptpython --with 'rich,sqlmodel'": "install ptpython",
    "pip install -U ptpython":"instal ptpython use pip",
    "pip install -U rich":"install rich use pip",
    "uv tool install -U ningfastforge":"fastapi 脚手架 forge",
    "uv tool install -U mcpm --python=3.11 --with 'pydantic==2.11.9'":"install mcpm",
    "uv tool install -U alembic":"Migration tool alembic",
    "uv tool install -U celery":"install celery",
    "uv tool install -U uvicorn":"install uvicorn",
    "uv tool install -U gunicorn":"install gunicorn",
    "uv tool install -U hypercorn":"install hypercorn",
}

node_pkgs = {
    "npm install -g opencode-ai@latest": "opencode",
    "npm install -g @iflow-ai/iflow-cli@latest":"iflow",
    "npm install -g @google/gemini-cli@latest":"gemini",
    "npm install -g @openai/codex@latest":"codex",
    "npm install -g add-skill@latest":"add-skill",
    "npm install -g skills@latest":"add skills",
    "npm install -g claude-code-templates@latest":"claude tempalte",
    "npm install -g uipro-cli@latest":"uipro",
    "npm install -g @lppx/nlearn@latest":"install nlearn",
    "npm install -g @lppx/webcamera@latest":"install webcamera"
    
}
# https://github.com/google-gemini/gemini-cli



cmds = {
    "bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)": "install 3xui",
}

bash_cmds={
    "xdg-mime query filetype xxx.txt":"get filetype ",
    "file --mime-type xxx":"file get filetype",
    "xdg-mime query default application/json":"get default application",
    "xdg-settings --list":"list 默认工具设置",
    "cat ~/.config/mimeapps.list":"list 我的默认工具",
    "xdg-mime default code.desktop application/json":"setting default tool"
}

powershell_cmds={
    "get-command python":"find exe path",
    "gcm git":"find git path",
    
}

winget_pkgs = {
    "winget install --id Python.Python.3.13 --custom 'PrependPath=1'":"(win)install python",
    "winget install --id=SQLite.SQLite": "(win) install sqlite",
    "winget install --id=Google.Chrome.Beta.EXE": "(win) install Google Chrome Beta",
    "winget install --id=7zip.7zip": "(win) install 7-Zip",
    "winget install --id=Notion.Notion -e": "(win) install Notion",
    "winget install --id=Yuanli.uTools -e": "(win) install uTools",
    "winget install --id=liule.Snipaste -e": "(win) install Snipaste",
    "winget install --id=File-New-Project.EarTrumpet -e": "(win) install EarTrumpet",
    "winget install --id=JiLuo.Xterminal -e": "(win) install Xterminal",
    "winget install --id=Git.Git -e": "(win) install Git",
    "winget install --id=GitHub.GitHubDesktop -e": "(win) install GitHub Desktop",
    "winget install --id=TortoiseGit.TortoiseGit -e": "(win) install TortoiseGit",
    "winget install --id=Microsoft.WindowsTerminal.Preview": "(win) install Windows Terminal Preview",
    "winget install --id=SublimeHQ.SublimeText.4 -e": "(win) install Sublime Text 4",
    "winget install --id=Microsoft.Edit -e": "(win) install Microsoft Edit",
    "winget install --force Microsoft.VisualStudioCode --override '/VERYSILENT /SP- /MERGETASKS=\"addcontextmenufiles,addcontextmenufolders,associatewithfiles,addtopath\"'": "(win) install VS Code with context menu",
    "winget install --id=Amazon.Kiro -e --override '/VERYSILENT /SP- /MERGETASKS=\"addcontextmenufiles,addcontextmenufolders,addtopath\"'": "(win) install Kiro with context menu",
    "winget install --id=kangfenmao.CherryStudio -e": "(win) install Cherry Studio",
    "winget install --id=ByteDance.Doubao -e": "(win) install Doubao",
    "winget install --id=Hashicorp.Vagrant -e": "(win) install Vagrant",
    "winget install --id=Oracle.VirtualBox -e": "(win) install VirtualBox",
    "winget install --id=astral-sh.uv -e": "(win) install uv",
    "winget install --id=CoreyButler.NVMforWindows -e": "(win) install NVM for Windows",
    "winget install --id=Tyrrrz.LightBulb -e": "(win) install LightBulb",
    "winget install --id=JetBrains.DataGrip -e": "(win) install DataGrip (free for non-commercial use)",
    "winget install --id=Microsoft.PowerShell -e": "(win) install PowerShell",
    "winget install --id=Warp.Warp -e": "(win) install Warp",
    "winget install --id=XiaoweiCloud.CalendarTask -e": "(win) install Calendar Task",
    "winget install --id voidtools.Everything -e":"(win) install everything",
    "winget install --id=Anthropic.Claude -e": "(win) install Claude",
    "winget install --id=ZhipuAI.AutoGLM -e":"(win) install zhipu autoglm",
    
    
    "winget install --id=XPDNH1FMW7NB40  -e --accept-package-agreements":"(win) install huorong",
    "winget install XPFCKBRNFZQ62G --accept-package-agreements":"(win) install wechat",
    "winget install Tencent.Foxmail":"(win) install foxmail",
    "winget install XP88XQLH1SDG81 --accept-package-agreements":"(win) install wangyimail",
    "winget install --id=lyswhut.lx-music-desktop -e":"(win) install lx music",

}

# key 当中不能存在空格 要不然就是无效选择  