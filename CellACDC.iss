;----------------------------------
; Inno Setup script for Cell-ACDC
;----------------------------------

[Setup]
AppName=Cell-ACDC
AppVersion=ACDC_VERSION
DefaultDirName={localappdata}\Cell-ACDC
DefaultGroupName=Cell-ACDC
OutputBaseFilename=Cell-ACDC-VERSION_NO_POINTS-Setup
Compression=lzma2/fast
UninstallDisplayIcon={app}\Cell-ACDC.exe
UninstallFilesDir={app}\uninstall
// UninstallDisplayName=Cell-ACDC-VERSION_NO_POINTS-Uninstaller
SolidCompression=yes
DisableProgramGroupPage=no
DisableDirPage=no
DisableWelcomePage=no
AlwaysShowDirOnReadyPage=yes
ExtraDiskSpaceRequired=11000000000
AppPublisher=schmollerlab
AppPublisherURL=https://github.com/SchmollerLab/Cell_ACDC

[Files]
; These are the compiled EXEs from your PyInstaller build
Source: "dist\Cell-ACDC-installer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Cell-ACDC.exe"; DestDir: "{app}"; Flags: ignoreversion

; Include miniforge only when using default Miniforge (not custom)
Source: "MINIFORGE_SOURCE\*"; DestDir: "{app}\miniforge"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: ShouldInstallMiniforge

; Include embedded CellACDC files if using bundles CellACDC
Source: "CELLACDC_SOURCE"; DestDir: "{app}"; Flags: ignoreversion; Check: ShouldInstallEmbeddedCellACDC

; Include portable Git if using GitHub installation
Source: "GIT_SOURCE\*"; DestDir: "{app}\portable_git"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: ShouldInstallGitHub

[UninstallDelete]
; Standard deletion (immediate) - remove deleteafterreboot flags as well handle this in code
Type: filesandordirs; Name: "{app}\cellacdc"
Type: filesandordirs; Name: "{app}\install_details.json"
Type: filesandordirs; Name: "{app}\installation_command.txt"
Type: filesandordirs; Name: "{app}\CellACDC_logs"
Type: filesandordirs; Name: "{app}\venv"
Type: filesandordirs; Name: "{app}\miniforge"
Type: filesandordirs; Name: "{app}\conda_venv"
Type: files; Name: "{app}\Cell-ACDC.exe"
Type: files; Name: "{app}\Cell-ACDC-installer.exe"
Type: files; Name: "{app}\*.dll"
Type: files; Name: "{app}\*.pyd"
Type: files; Name: "{app}\*.pyc"
Type: filesandordirs; Name: "{app}\__pycache__"
Type: filesandordirs; Name: "{app}\*.tmp"
Type: dirifempty; Name: "{app}"


[Icons]
; Shortcut to launch Cell-ACDC
Name: "{group}\Cell-ACDC"; \
  Filename: "{app}\Cell-ACDC.exe"; \
  Parameters: "--target ""{app}"""; \
  WorkingDir: "{app}"; \
  IconFilename: "{app}\Cell-ACDC.exe"; \
  Comment: "Run the Cell-ACDC GUI"

; Optional desktop shortcut
Name: "{commondesktop}\Cell-ACDC"; \
  Filename: "{app}\Cell-ACDC.exe"; \
  Parameters: "--target ""{app}"""; \
  WorkingDir: "{app}"; \
  IconFilename: "{app}\Cell-ACDC.exe"; \
  Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
; Run the installer immediately after install with elevated rights
Filename: "{app}\Cell-ACDC-installer.exe"; \
  Parameters: "--target ""{app}"" --use_github ""{code:GetGitHubFlag}"" --version ""{code:GetVersionValue}"" --python_path ""{code:GetPythonPath}"" --embeddedpyflag ""{code:GetPythonInstallFlag}"" --pyversion PLACEHOLDER_PY_VER --custom_CellACDC_path ""{code:GetCustomCellACDCPath}"""; \
  Description: "Install Cell-ACDC now (Please monitor the command terminal for progress)"; \
  Flags: shellexec waituntilterminated; \
  Verb: runas; \
  BeforeInstall: SaveInstallationCommand

[Code]
// Windows API declarations for scheduled deletion
const
  MOVEFILE_DELAY_UNTIL_REBOOT = $4;

function MoveFileEx(lpExistingFileName, lpNewFileName: WideString; dwFlags: DWORD): BOOL;
external 'MoveFileExW@kernel32.dll stdcall';

// Helper function to try regular deletion first, then schedule deletion
procedure TryDeleteWithFallback(Path: string; IsDirectory: Boolean);
var
  Success: Boolean;
begin
  Success := False;
  
  if IsDirectory then
  begin
    if DirExists(Path) then
    begin
      Success := DelTree(Path, True, True, True);
      if not Success then
      begin
        Log('Failed to delete directory immediately, scheduling for reboot: ' + Path);
        MoveFileEx(Path, '', MOVEFILE_DELAY_UNTIL_REBOOT);
      end
      else
      begin
        Log('Successfully deleted directory: ' + Path);
      end;
    end;
  end
  else
  begin
    if FileExists(Path) then
    begin
      Success := DeleteFile(Path);
      if not Success then
      begin
        Log('Failed to delete file immediately, scheduling for reboot: ' + Path);
        MoveFileEx(Path, '', MOVEFILE_DELAY_UNTIL_REBOOT);
      end
      else
      begin
        Log('Successfully deleted file: ' + Path);
      end;
    end;
  end;
end;

// Handle uninstall steps
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDir: string;
begin
  if CurUninstallStep = usPostUninstall then 
  begin
    AppDir := ExpandConstant('{app}');
    Log('Starting enhanced deletion process for: ' + AppDir);
    
    // Try to delete directories that might be locked
    TryDeleteWithFallback(AppDir + '\venv', True);
    TryDeleteWithFallback(AppDir + '\miniforge', True);
    TryDeleteWithFallback(AppDir + '\conda_venv', True);
    
    // Try to delete executables that might be in use
    TryDeleteWithFallback(AppDir + '\Cell-ACDC.exe', False);
    TryDeleteWithFallback(AppDir + '\Cell-ACDC-installer.exe', False);
    
    // Try to delete any remaining DLL and PYD files
    if DirExists(AppDir) then
    begin
      // Note: For wildcard patterns, we'd need to enumerate files
      // This is a simplified approach for the main directory
      if FileExists(AppDir + '\python.dll') then
        TryDeleteWithFallback(AppDir + '\python.dll', False);
      if FileExists(AppDir + '\python3.dll') then
        TryDeleteWithFallback(AppDir + '\python3.dll', False);
    end;
    
    // Final attempt to remove the app directory if empty
    if DirExists(AppDir) then
    begin
      if not RemoveDir(AppDir) then
      begin
        Log('App directory not empty or locked, scheduling for reboot: ' + AppDir);
        MoveFileEx(AppDir, '', MOVEFILE_DELAY_UNTIL_REBOOT);
      end
      else
      begin
        Log('Successfully removed app directory: ' + AppDir);
      end;
    end;
    
    Log('Enhanced deletion process completed');
  end;
end;

var
  UseGitHubCheckbox: TNewCheckBox;
  UseEmbeddedCheckbox: TNewCheckBox;
  InfoLabel: TNewStaticText;
  SpaceLabel: TNewStaticText;
  VersionCombo: TNewComboBox;
  VersionComboText: TNewStaticText;
  
  // Custom Python page variables
  CustomPythonPage: TWizardPage;
  UseCustomPythonCheckbox: TNewCheckBox;
  PythonPathLabel: TNewStaticText;
  PythonPathEdit: TNewEdit;
  PythonPathBrowseButton: TNewButton;
  CustomPythonInfoLabel: TNewStaticText;
  
  // Custom CellACDC path variables
  CustomCellACDCCheckbox: TNewCheckBox;
  CustomCellACDCPathLabel: TNewStaticText;
  CustomCellACDCPathEdit: TNewEdit;
  CustomCellACDCPathBrowseButton: TNewButton;
  
  // Control initialization flags
  CustomPythonPageInitialized: Boolean;
  SelectDirPageInitialized: Boolean;
  SelectCellACDCInstallPageInitialized: Boolean;
  
  // GitHub button on finish page
  GitHubButton: TNewButton;
  
  // Installation info label
  InstallInfoLabel: TNewStaticText;
  
  // New variables for Cell-ACDC source selection page
  CellACDCPage: TWizardPage;

procedure InitializeWizard;
begin
  // Just create the controls, don't configure them yet
  UseGitHubCheckbox := TNewCheckBox.Create(WizardForm);
  InfoLabel := TNewStaticText.Create(WizardForm);
  SpaceLabel := TNewStaticText.Create(WizardForm);
  VersionCombo := TNewComboBox.Create(WizardForm);
  
  // Create custom Miniforge path page
  CustomPythonPage := CreateCustomPage(wpSelectDir, 'Conda Configuration', 'Choose your conda installation');
  
  // Create custom Cell-ACDC selection page
  CellACDCPage := CreateCustomPage(wpSelectDir, 'Cell-ACDC Source', 'Choose your Cell-ACDC installation source');
  
  // Create custom Python path controls
  UseCustomPythonCheckbox := TNewCheckBox.Create(WizardForm);
  PythonPathLabel := TNewStaticText.Create(WizardForm);
  PythonPathEdit := TNewEdit.Create(WizardForm);
  PythonPathBrowseButton := TNewButton.Create(WizardForm);
  CustomPythonInfoLabel := TNewStaticText.Create(WizardForm);
  
  // Initialize flags
  CustomPythonPageInitialized := False;
  SelectDirPageInitialized := False;
end;

procedure UseGitHubCheckboxClick(Sender: TObject);
begin
  if UseGitHubCheckbox.Checked then
  begin
    UseEmbeddedCheckbox.Checked := False; // Disable embedded checkbox if using GitHub
    CustomCellACDCCheckbox.Checked := False; // Disable custom checkbox if using GitHub
    VersionCombo.Enabled := False; // Disable version selection if using GitHub
    VersionComboText.Font.Color := clGray;
  end
  else if not UseEmbeddedCheckbox.Checked and not CustomCellACDCCheckbox.Checked then
  begin
    VersionCombo.Enabled := True; // Enable version selection if not using GitHub, embedded, or custom
    VersionComboText.Font.Color := clWindowText;
  end
  else
    VersionComboText.Font.Color := clGray;
end;

procedure UseEmbeddedCellACDCCheckboxClick(Sender: TObject);
begin
  if UseEmbeddedCheckbox.Checked then
  begin
    UseGitHubCheckbox.Checked := False; // Disable GitHub checkbox if using embedded
    CustomCellACDCCheckbox.Checked := False; // Disable custom checkbox if using embedded
    VersionCombo.Enabled := False; // Disable version selection if using embedded
    VersionComboText.Font.Color := clGray;
  end
  else if not UseGitHubCheckbox.Checked and not CustomCellACDCCheckbox.Checked then
  begin
    VersionCombo.Enabled := True; // Enable version selection if not using GitHub, embedded, or custom
    VersionComboText.Font.Color := clWindowText;
  end
  else
    VersionComboText.Font.Color := clGray;
end;

procedure UseCustomPythonCheckboxClick(Sender: TObject);
begin
  PythonPathLabel.Enabled := UseCustomPythonCheckbox.Checked;
  PythonPathEdit.Enabled := UseCustomPythonCheckbox.Checked;
  PythonPathBrowseButton.Enabled := UseCustomPythonCheckbox.Checked;
  if UseCustomPythonCheckbox.Checked then
  begin
    PythonPathLabel.Font.Color := clWindowText;
  end
  else
  begin
    PythonPathLabel.Font.Color := clGray;
  end;
end;

procedure PythonPathBrowseButtonClick(Sender: TObject);
var
  FolderPath: string;
begin
  if BrowseForFolder('Select Conda Installation Folder', FolderPath, False) then
  begin
    PythonPathEdit.Text := FolderPath;
  end;
end;

procedure CustomCellACDCCheckboxClick(Sender: TObject);
begin
  CustomCellACDCPathLabel.Enabled := CustomCellACDCCheckbox.Checked;
  CustomCellACDCPathEdit.Enabled := CustomCellACDCCheckbox.Checked;
  CustomCellACDCPathBrowseButton.Enabled := CustomCellACDCCheckbox.Checked;
  if CustomCellACDCCheckbox.Checked then
  begin
    CustomCellACDCPathLabel.Font.Color := clWindowText;
    UseGitHubCheckbox.Checked := False; // Disable GitHub checkbox if using custom
    UseEmbeddedCheckbox.Checked := False; // Disable embedded checkbox if using custom
    VersionCombo.Enabled := False; // Disable version selection if using custom
    VersionComboText.Font.Color := clGray;
  end
  else if not UseGitHubCheckbox.Checked and not UseEmbeddedCheckbox.Checked then
  begin
    CustomCellACDCPathLabel.Font.Color := clGray;
    VersionCombo.Enabled := True; // Enable version selection if not using GitHub, embedded, or custom
    VersionComboText.Font.Color := clWindowText;
  end
  else
  begin
    CustomCellACDCPathLabel.Font.Color := clGray;
    VersionComboText.Font.Color := clGray;
  end;
end;

procedure CustomCellACDCPathBrowseButtonClick(Sender: TObject);
var
  FolderPath: string;
begin
  if BrowseForFolder('Select Cell-ACDC Repository Folder', FolderPath, False) then
    CustomCellACDCPathEdit.Text := FolderPath;
end;

procedure GitHubButtonClick(Sender: TObject);
var
  ErrorCode: Integer;
begin
  ShellExec('open', 'https://github.com/SchmollerLab/Cell_ACDC', '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpWelcome then
  begin
    WizardForm.WelcomeLabel2.Caption := 
      'This will install Cell-ACDC on your computer.' + #13#10 +
      'It is recommended that you close all other applications' + #13#10 +
      'before continuing.' + #13#10 + #13#10 +
      'This installer was created using Inno Setup,' + #13#10 +
      'and contains a distribution of Miniforge Python' + #13#10 +
      'and Portable Git.' + #13#10 + #13#10 +
      'Click Next to continue, or Cancel to exit Setup.';

    // Set the label height first to accommodate the new content
    WizardForm.WelcomeLabel2.Height := ScaleY(120);  // Increase height for more lines with spacing
    
    // Add GitHub button to welcome page positioned below the welcome text
    GitHubButton := TNewButton.Create(WizardForm);
    GitHubButton.Parent := WizardForm.WelcomePage;
    GitHubButton.Caption := 'Open GitHub Page';
    GitHubButton.Left := WizardForm.WelcomeLabel2.Left;  // Align with welcome text
    GitHubButton.Top := WizardForm.WelcomeLabel2.Top + WizardForm.WelcomeLabel2.Height + ScaleY(15);  // Below welcome text
    GitHubButton.Width := ScaleX(120);
    GitHubButton.Height := ScaleY(23);
    GitHubButton.OnClick := @GitHubButtonClick;
    GitHubButton.Visible := True;
  end
  else if (CurPageID = CellACDCPage.ID) and not SelectCellACDCInstallPageInitialized then
  begin

    // Add an info label
    InfoLabel.Parent := CellACDCPage.Surface;
    InfoLabel.Caption := 'This will determine how Cell-ACDC is installed on your system.';
    InfoLabel.Top := ScaleY(5);
    InfoLabel.Left := WizardForm.DirEdit.Left;
    InfoLabel.Width := ScaleX(400);
    InfoLabel.Height := ScaleY(15);
    InfoLabel.Visible := True;
    
    // Add storage space information
    SpaceLabel.Parent := CellACDCPage.Surface;
    SpaceLabel.Caption := 'For latest features and bug fixes, GitHub installation is recommended.';
    SpaceLabel.Top := InfoLabel.Top + InfoLabel.Height;
    SpaceLabel.Left := WizardForm.DirEdit.Left;
    SpaceLabel.Width := ScaleX(400);
    SpaceLabel.Height := ScaleY(15);
    SpaceLabel.Visible := True;

    // Configure the checkbox only once
    UseGitHubCheckbox.Parent := CellACDCPage.Surface;
    UseGitHubCheckbox.Caption := 'Install Cell-ACDC from GitHub';
    UseGitHubCheckbox.Checked := True;
    UseGitHubCheckbox.Top := SpaceLabel.Top + SpaceLabel.Height + ScaleY(15);
    UseGitHubCheckbox.Left := WizardForm.DirEdit.Left;
    UseGitHubCheckbox.Width := ScaleX(400);
    UseGitHubCheckbox.Height := ScaleY(17);
    UseGitHubCheckbox.Visible := True;
    UseGitHubCheckbox.OnClick := @UseGitHubCheckboxClick;

    // Create mutually exclusive checkbox for embedded Cell-ACDC
    UseEmbeddedCheckbox := TNewCheckBox.Create(WizardForm);
    UseEmbeddedCheckbox.Parent := CellACDCPage.Surface;
    UseEmbeddedCheckbox.Caption := 'Install embedded Cell-ACDC (ACDC_VERSION)';
    UseEmbeddedCheckbox.Checked := False;
    UseEmbeddedCheckbox.Top := UseGitHubCheckbox.Top + UseGitHubCheckbox.Height + ScaleY(5);
    UseEmbeddedCheckbox.Left := WizardForm.DirEdit.Left;
    UseEmbeddedCheckbox.Width := ScaleX(400);
    UseEmbeddedCheckbox.Height := ScaleY(17);
    UseEmbeddedCheckbox.Visible := True;
    UseEmbeddedCheckbox.OnClick := @UseEmbeddedCellACDCCheckboxClick;
    
    // Add custom CellACDC path selector
    CustomCellACDCCheckbox := TNewCheckBox.Create(WizardForm.SelectDirPage);
    CustomCellACDCCheckbox.Parent := CellACDCPage.Surface;
    CustomCellACDCCheckbox.Caption := 'Use custom Cell-ACDC repository path';
    CustomCellACDCCheckbox.Checked := False;
    CustomCellACDCCheckbox.Top := UseEmbeddedCheckbox.Top + UseEmbeddedCheckbox.Height + ScaleY(5);
    CustomCellACDCCheckbox.Left := WizardForm.DirEdit.Left;
    CustomCellACDCCheckbox.Width := ScaleX(400);
    CustomCellACDCCheckbox.Height := ScaleY(17);
    CustomCellACDCCheckbox.Visible := True;
    CustomCellACDCCheckbox.OnClick := @CustomCellACDCCheckboxClick;

    CustomCellACDCPathLabel := TNewStaticText.Create(WizardForm.SelectDirPage);
    CustomCellACDCPathLabel.Parent := CellACDCPage.Surface;
    CustomCellACDCPathLabel.Caption := 'Cell-ACDC repository folder path:';
    CustomCellACDCPathLabel.Top := CustomCellACDCCheckbox.Top + CustomCellACDCCheckbox.Height + ScaleY(5);
    CustomCellACDCPathLabel.Left := WizardForm.DirEdit.Left;
    CustomCellACDCPathLabel.Width := ScaleX(200);
    CustomCellACDCPathLabel.Height := ScaleY(17);
    CustomCellACDCPathLabel.Visible := True;
    CustomCellACDCPathLabel.Enabled := False;
    CustomCellACDCPathLabel.Font.Color := clGray;

    CustomCellACDCPathEdit := TNewEdit.Create(WizardForm.SelectDirPage);
    CustomCellACDCPathEdit.Parent := CellACDCPage.Surface;
    CustomCellACDCPathEdit.Top := CustomCellACDCPathLabel.Top + CustomCellACDCPathLabel.Height + ScaleY(2);
    CustomCellACDCPathEdit.Left := WizardForm.DirEdit.Left;
    CustomCellACDCPathEdit.Width := ScaleX(300);
    CustomCellACDCPathEdit.Height := ScaleY(21);
    CustomCellACDCPathEdit.Visible := True;
    CustomCellACDCPathEdit.Enabled := False;
    CustomCellACDCPathEdit.Text := '';

    CustomCellACDCPathBrowseButton := TNewButton.Create(WizardForm.SelectDirPage);
    CustomCellACDCPathBrowseButton.Parent := CellACDCPage.Surface;
    CustomCellACDCPathBrowseButton.Caption := 'Browse...';
    CustomCellACDCPathBrowseButton.Top := CustomCellACDCPathEdit.Top;
    CustomCellACDCPathBrowseButton.Left := CustomCellACDCPathEdit.Left + CustomCellACDCPathEdit.Width + ScaleX(10);
    CustomCellACDCPathBrowseButton.Width := ScaleX(75);
    CustomCellACDCPathBrowseButton.Height := ScaleY(23);
    CustomCellACDCPathBrowseButton.Visible := True;
    CustomCellACDCPathBrowseButton.Enabled := False;
    CustomCellACDCPathBrowseButton.OnClick := @CustomCellACDCPathBrowseButtonClick;

    // Create version selection info text and combo box
    VersionComboText := TNewStaticText.Create(WizardForm);
    VersionComboText.Parent := CellACDCPage.Surface;
    VersionComboText.Caption := 'Select Cell-ACDC version for PyPi installation:';
    VersionComboText.Top := CustomCellACDCPathEdit.Top + CustomCellACDCPathEdit.Height + ScaleY(15);
    VersionComboText.Left := WizardForm.DirEdit.Left;
    VersionComboText.Width := ScaleX(300);
    VersionComboText.Height := ScaleY(17);
    VersionComboText.Font.Color := clGray;
    VersionComboText.Visible := True;

    VersionCombo.Parent := CellACDCPage.Surface;
    ACDC_AVAILABLE_VERSIONS
    VersionCombo.ItemIndex := 0; // Select first item (ACDC_VERSION) by default
    VersionCombo.Style := csDropDownList; // Make it read-only dropdown
    VersionCombo.Top := VersionComboText.Top + VersionComboText.Height + ScaleY(2);
    VersionCombo.Left := WizardForm.DirEdit.Left;
    VersionCombo.Width := ScaleX(120);
    VersionCombo.Height := ScaleY(21);
    VersionCombo.Visible := True;
    VersionCombo.Enabled := not UseGitHubCheckbox.Checked and not UseEmbeddedCheckbox.Checked; // Disable if using GitHub or embedded Cell-ACDC

    SelectCellACDCInstallPageInitialized := True;
  end
  else if (CurPageID = CustomPythonPage.ID) and not CustomPythonPageInitialized then
  begin
    // Configure custom Python page controls only once
    UseCustomPythonCheckbox.Parent := CustomPythonPage.Surface;
    UseCustomPythonCheckbox.Caption := 'Use custom conda installation';
    UseCustomPythonCheckbox.Checked := False;
    UseCustomPythonCheckbox.Top := ScaleY(5);
    UseCustomPythonCheckbox.Left := WizardForm.DirEdit.Left;
    UseCustomPythonCheckbox.Width := ScaleX(400);
    UseCustomPythonCheckbox.Height := ScaleY(17);
    UseCustomPythonCheckbox.Visible := True;
    UseCustomPythonCheckbox.OnClick := @UseCustomPythonCheckboxClick;
    
    // Python path label
    PythonPathLabel.Parent := CustomPythonPage.Surface;
    PythonPathLabel.Caption := 'Conda installation folder path:';
    PythonPathLabel.Top := UseCustomPythonCheckbox.Top + UseCustomPythonCheckbox.Height + ScaleY(5);
    PythonPathLabel.Left := WizardForm.DirEdit.Left;
    PythonPathLabel.Width := ScaleX(150);
    PythonPathLabel.Height := ScaleY(17);
    PythonPathLabel.Visible := True;
    PythonPathLabel.Enabled := False;
    PythonPathLabel.Font.Color := clGray;
    
    // Python path edit box
    PythonPathEdit.Parent := CustomPythonPage.Surface;
    PythonPathEdit.Top := PythonPathLabel.Top + PythonPathLabel.Height + ScaleY(2);
    PythonPathEdit.Left := WizardForm.DirEdit.Left;
    PythonPathEdit.Width := ScaleX(300);
    PythonPathEdit.Height := ScaleY(21);
    PythonPathEdit.Visible := True;
    PythonPathEdit.Enabled := False;
    PythonPathEdit.Text := '';
    
    // Browse button
    PythonPathBrowseButton.Parent := CustomPythonPage.Surface;
    PythonPathBrowseButton.Caption := 'Browse...';
    PythonPathBrowseButton.Top := PythonPathEdit.Top;
    PythonPathBrowseButton.Left := PythonPathEdit.Left + PythonPathEdit.Width + ScaleX(10);
    PythonPathBrowseButton.Width := ScaleX(75);
    PythonPathBrowseButton.Height := ScaleY(23);
    PythonPathBrowseButton.Visible := True;
    PythonPathBrowseButton.Enabled := False;
    PythonPathBrowseButton.OnClick := @PythonPathBrowseButtonClick;
    
    // Info label
    CustomPythonInfoLabel.Parent := CustomPythonPage.Surface;
    CustomPythonInfoLabel.Caption := 'Choose your conda installation option:' + #13#10 +
                                     '• Default: Use the Miniforge included with Cell-ACDC (recommended)' + #13#10 +
                                     '• Custom: Specify your own conda installation folder'  + #13#10 + 
                                     '(Miniforge, Anaconda, or Miniconda)';
    CustomPythonInfoLabel.Top := PythonPathEdit.Top + PythonPathEdit.Height + ScaleY(15);
    CustomPythonInfoLabel.Left := WizardForm.DirEdit.Left;
    CustomPythonInfoLabel.Width := ScaleX(400);
    CustomPythonInfoLabel.Height := ScaleY(68);
    CustomPythonInfoLabel.Font.Color := clGray;
    CustomPythonInfoLabel.Visible := True;
    
    CustomPythonPageInitialized := True;
  end
  else if CurPageID = wpReady then
  begin
    // Add installation configuration info to the Ready page
    WizardForm.ReadyMemo.Lines.Add('');
    WizardForm.ReadyMemo.Lines.Add('Installation Configuration:');
    if CustomCellACDCCheckbox.Checked then
    begin
      WizardForm.ReadyMemo.Lines.Add('    Source: Custom repository path');
      WizardForm.ReadyMemo.Lines.Add('    Path: ' + CustomCellACDCPathEdit.Text);
    end
    else if UseEmbeddedCheckbox.Checked then
    begin
      WizardForm.ReadyMemo.Lines.Add('    Source: Embedded Cell-ACDC');
      WizardForm.ReadyMemo.Lines.Add('    Version: ACDC_VERSION');
    end
    else if UseGitHubCheckbox.Checked then
    begin
      WizardForm.ReadyMemo.Lines.Add('    Source: GitHub (latest development version)');
    end
    else
    begin
      WizardForm.ReadyMemo.Lines.Add('    Source: PyPI (stable release)');
      WizardForm.ReadyMemo.Lines.Add('    Version: ' + VersionCombo.Text);
    end;

    // Add Python configuration info
    WizardForm.ReadyMemo.Lines.Add('');
    WizardForm.ReadyMemo.Lines.Add('Python Configuration:');
    if UseCustomPythonCheckbox.Checked then
    begin
      WizardForm.ReadyMemo.Lines.Add('    Miniforge: Custom installation');
      WizardForm.ReadyMemo.Lines.Add('    Path: ' + PythonPathEdit.Text);
      WizardForm.ReadyMemo.Lines.Add('    Note: Bundled Miniforge will not be installed');
    end
    else
    begin
      WizardForm.ReadyMemo.Lines.Add('    Miniforge: Default (bundled with Cell-ACDC)');
      WizardForm.ReadyMemo.Lines.Add('    Location: Installation directory\miniforge');
    end;
  end
  else if CurPageID = wpInstalling then
  begin
    // Add installation info text below the progress bar
    if not Assigned(InstallInfoLabel) then
    begin
      InstallInfoLabel := TNewStaticText.Create(WizardForm);
      InstallInfoLabel.Parent := WizardForm.InstallingPage;
      InstallInfoLabel.Caption := 
        'After unpacking, Python scripts will run automatically to complete the installation.' + #13#10 +
        'This may take a while.' + #13#10 + #13#10 +
        'IMPORTANT NOTES:' + #13#10 +
        '• A command terminal will open after unpacking is done - please monitor it for' + #13#10 +
        '  installation progress' + #13#10 +
        '• Do not close the terminal window during installation' + #13#10 +
        '• The installation command is saved to "installation_command.txt"' + #13#10 +
        '• If something goes wrong, you can run "Cell-ACDC-installer.exe" to retry' + #13#10 +
        '• If you encounter any errors, please contact us! We are always happy to help!';
      InstallInfoLabel.Left := WizardForm.ProgressGauge.Left;
      InstallInfoLabel.Top := WizardForm.ProgressGauge.Top + WizardForm.ProgressGauge.Height + ScaleY(10);
      InstallInfoLabel.Width := ScaleX(400);
      InstallInfoLabel.Height := ScaleY(140);
      InstallInfoLabel.Font.Color := clWindowText;
    end;
    
    // Add GitHub button during installation too
    if not Assigned(GitHubButton) or (GitHubButton.Parent <> WizardForm.InstallingPage) then
    begin
      GitHubButton := TNewButton.Create(WizardForm);
      GitHubButton.Parent := WizardForm.InstallingPage;
      GitHubButton.Caption := 'Open GitHub Page';
      GitHubButton.Left := InstallInfoLabel.Left;
      GitHubButton.Top := InstallInfoLabel.Top + InstallInfoLabel.Height - ScaleY(5);
      GitHubButton.Width := ScaleX(120);
      GitHubButton.Height := ScaleY(23);
      GitHubButton.OnClick := @GitHubButtonClick;
    end;
  end
  else if CurPageID = wpFinished then
  begin
    // Add custom message on finish page
    // Add custom message on finish page
    WizardForm.FinishedLabel.Caption := 
      'Cell-ACDC installation script is now completed!' + #13#10 +
      'If there was an error, please contact us!' + #13#10 + #13#10 +
      'IMPORTANT NOTES:' + #13#10 +
      '• You can now launch Cell-ACDC from the Start menu' + #13#10 +
      '   or desktop shortcut' + #13#10 +
      '• If you encountered any errors, please contact us!' + #13#10 +
      '   We are always happy to help!' + #13#10 +
      '• Visit our GitHub page for support and documentation' + #13#10 +
      '• The installation command is saved to'  + #13#10 +
      '   "installation_command.txt"' + #13#10 +
      '• If something goes wrong, you can run' + #13#10 +
      '   "Cell-ACDC-installer.exe" to retry' + #13#10 +
      '• The command and .exe are saved in the installation directory' + #13#10 +
      '   '+ExpandConstant('{app}')
    WizardForm.FinishedLabel.Height := ScaleY(200); // Increase height for more lines with spacing
    
    // Add clickable GitHub button (create new instance for finish page)
    GitHubButton := TNewButton.Create(WizardForm);
    GitHubButton.Parent := WizardForm.FinishedPage;
    GitHubButton.Caption := 'Open GitHub Page';
    GitHubButton.Left := WizardForm.FinishedLabel.Left;
    GitHubButton.Top := WizardForm.FinishedLabel.Top + WizardForm.FinishedLabel.Height + ScaleY(7);
    GitHubButton.Width := ScaleX(120);
    GitHubButton.Height := ScaleY(23);
    GitHubButton.OnClick := @GitHubButtonClick;
  end;
end;

function GetPythonInstallFlag(Param: string): string;
begin
  if UseCustomPythonCheckbox.Checked then
    Result := 'false'  // Custom Python installation, do not install Miniforge
  else
    Result := 'true';   // Use bundled Miniforge Python
end;

function ShouldInstallMiniforge: Boolean;
begin
  Result := not UseCustomPythonCheckbox.Checked;
end;

function ShouldInstallEmbeddedCellACDC: Boolean;
begin
  Result := UseEmbeddedCheckbox.Checked; // Use embedded Cell-ACDC
end;

function GetGitHubFlag(Param: string): string;
begin
  if UseGitHubCheckbox.Checked then
    Result := 'true'
  else
    Result := 'false';
end;

function GetVersionValue(Param: string): string;
begin
  if VersionCombo.Enabled then
    Result := VersionCombo.Text
  else
    Result := 'NA';
end;

function GetPythonPath(Param: string): string;
begin
  if UseCustomPythonCheckbox.Checked then
    Result := PythonPathEdit.Text + '\python.exe'
  else 
    Result := ExpandConstant('{app}\miniforge\python.exe');  // Use bundled miniforge Python
end;

function GetCustomCellACDCPath(Param: string): string;
begin
  if CustomCellACDCCheckbox.Checked then
  begin
    Result := CustomCellACDCPathEdit.Text;
  end
  else if UseEmbeddedCheckbox.Checked then
  begin
    Result := ExpandConstant('{app}\CELLACDC_FILE_NAME');
  end
  else
  begin
    Result := 'DEFAULT';
  end
end;

procedure SaveInstallationCommand;
var
  CommandFile: string;
  Command: string;
  FileContent: string;
begin
  CommandFile := ExpandConstant('{app}\installation_command.txt');
  
  // Build the exact command that will be executed
  Command := '"' + ExpandConstant('{app}') + '\Cell-ACDC-installer.exe" ' +
             '--target "' + ExpandConstant('{app}') + '" ' +
             '--use_github "' + GetGitHubFlag('') + '" ' +
             '--version "' + GetVersionValue('') + '" ' +
             '--python_path "' + GetPythonPath('') + '" ' +
             '--embeddedpyflag "' + GetPythonInstallFlag('') + '" ' +
             '--pyversion PLACEHOLDER_PY_VER' +
             ' --custom_CellACDC_path "' + GetCustomCellACDCPath('') + '"';
  
  // Create file content with explanation
  FileContent := 'Cell-ACDC Installation Command' + #13#10 +
                '================================' + #13#10 + #13#10 +
                'If the installation failed or you need to reinstall Cell-ACDC,' + #13#10 +
                'you can copy and paste the following command into a Command Prompt' + #13#10 +
                'opened as Administrator:' + #13#10 + #13#10 +
                Command + #13#10 + #13#10 +
                'Instructions:' + #13#10 +
                '1. Press Windows key + R' + #13#10 +
                '2. Type "cmd" and press Ctrl+Shift+Enter (to run as Administrator)' + #13#10 +
                '3. Copy and paste the command above' + #13#10 +
                '4. Press Enter to execute' + #13#10 + #13#10 +
                'Generated on: ' + GetDateTimeString('yyyy-mm-dd hh:nn:ss', #0, #0) + #13#10 +
                'Installation Directory: ' + ExpandConstant('{app}') + #13#10;
  
  // Save to file
  try
    SaveStringToFile(CommandFile, FileContent, False);
    Log('Installation command saved to: ' + CommandFile);
  except
    Log('Failed to save installation command to file');
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  PythonExePath, CondaExePath: string;
begin
  Result := True;
  
  // Validate custom Python path if selected
  if (CurPageID = CustomPythonPage.ID) and UseCustomPythonCheckbox.Checked then
  begin
    if Trim(PythonPathEdit.Text) = '' then
    begin
      MsgBox('Please select a conda installation folder path or uncheck "Use custom conda installation".', mbError, MB_OK);
      Result := False;
    end
    else if not DirExists(PythonPathEdit.Text) then
    begin
      MsgBox('The specified folder does not exist. Please select a valid conda installation folder.', mbError, MB_OK);
      Result := False;
    end
    else
    begin
      PythonExePath := PythonPathEdit.Text + '\python.exe';
      CondaExePath := PythonPathEdit.Text + '\Scripts\conda.exe';
      if not FileExists(PythonExePath) then
      begin
        MsgBox('The selected conda folder does not contain python.exe. Please select a valid conda installation folder.', mbError, MB_OK);
        Result := False;
      end
      else if not FileExists(CondaExePath) then
      begin
        MsgBox('The selected conda folder does not contain \Scripts\conda.exe. Please select a valid conda installation folder.', mbError, MB_OK);
        Result := False;
      end;
    end;
  end
  // Validate custom CellACDC path if selected
  else if (CurPageID = CellACDCPage.ID) and CustomCellACDCCheckbox.Checked then
  begin
    if Trim(CustomCellACDCPathEdit.Text) = '' then
    begin
      MsgBox('Please select a Cell-ACDC Repository folder path or uncheck "Use custom Cell-ACDC Repository path".', mbError, MB_OK);
      Result := False;
    end
    else if not DirExists(CustomCellACDCPathEdit.Text) then
    begin
      MsgBox('The specified Cell-ACDC Repository folder does not exist. Please select a valid folder.', mbError, MB_OK);
      Result := False;
    end
    else if not DirExists(AddBackslash(CustomCellACDCPathEdit.Text) + 'cellacdc') then
    begin
      MsgBox('The selected folder does not contain a required subfolder named "cellacdc". Please select a valid Cell-ACDC Repository folder.', mbError, MB_OK);
      Result := False;
    end
    else if not FileExists(AddBackslash(CustomCellACDCPathEdit.Text) + 'pyproject.toml') then
    begin
      MsgBox('The selected folder does not contain a required file named "pyproject.toml". Please select a valid Cell-ACDC Repository folder.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function ShouldInstallGitHub: Boolean;
begin
  Result := UseGitHubCheckbox.Checked; // Return true if GitHub installation is selected
end;