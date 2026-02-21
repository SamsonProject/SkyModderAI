; ============================================================================
; SkyModderAI - xEdit Export Script
; Export conflict data from xEdit to SkyModderAI format
; ============================================================================
; Installation:
;   1. Copy this script to: <Game Folder>/Edit Scripts/SkyModderAI/
;   2. Run xEdit (SSEEdit, FO4Edit, etc.)
;   3. Right-click mod → Apply Script → SkyModderAI Export
; ============================================================================

unit SkyModderAI_Export;

interface

implementation

uses
  wbInterface, wbHelpers, wbRecords, wbRecordsEx;

const
  OUTPUT_FILE = 'SkyModderAI_Export.json';

type
  TModInfo = record
    ModName: string;
    FileName: string;
    Author: string;
    Version: string;
    Masters: TStringList;
    Conflicts: TStringList;
  end;

var
  OutputList: TStringList;
  ModInfo: TModInfo;

function Initialize: integer;
begin
  Result := 0;
  OutputList := TStringList.Create;
  ModInfo.Masters := TStringList.Create;
  ModInfo.Conflicts := TStringList.Create;
end;

procedure DeInitialize;
begin
  OutputList.Free;
  ModInfo.Masters.Free;
  ModInfo.Conflicts.Free;
end;

function GetModAuthor(aMainRecord: IwbMainRecord): string;
var
  Container: IwbContainer;
  SubRecord: IwbContainer;
  Element: IwbElement;
begin
  Result := '';
  
  // Try to get author from CNAM (TES4 header)
  if aMainRecord.Container <> nil then
  begin
    Element := aMainRecord.Container.ElementByName['CNAM'];
    if Element <> nil then
      Result := Element.Value;
  end;
  
  // Fallback to mod description
  if Result = '' then
  begin
    Element := aMainRecord.ElementByName['HEDR - Header'];
    if Element <> nil then
    begin
      SubRecord := Element.ElementByName['CNAM'];
      if SubRecord <> nil then
        Result := SubRecord.Value;
    end;
  end;
end;

function GetModVersion(aMainRecord: IwbMainRecord): string;
var
  Element: IwbElement;
begin
  Result := '1.0.0';
  
  // Try to get version from HEDR
  if aMainRecord.Container <> nil then
  begin
    Element := aMainRecord.Container.ElementByName['HEDR'];
    if Element <> nil then
    begin
      // Version is typically in user version or can be extracted from description
      Result := '1.0.0'; // Default, xEdit doesn't always expose version directly
    end;
  end;
end;

procedure ExportMod(aFile: IwbFile);
var
  MainRecord: IwbMainRecord;
  MasterCount: integer;
  i: integer;
  ConflictInfo: string;
begin
  if aFile = nil then Exit;
  
  MainRecord := aFile.MainRecord;
  if MainRecord = nil then Exit;
  
  // Get mod info
  ModInfo.ModName := aFile.Name;
  ModInfo.FileName := aFile.FileName;
  ModInfo.Author := GetModAuthor(MainRecord);
  ModInfo.Version := GetModVersion(MainRecord);
  
  // Get masters
  ModInfo.Masters.Clear;
  MasterCount := aFile.MasterCount;
  for i := 0 to MasterCount - 1 do
  begin
    ModInfo.Masters.Add(aFile.MasterFileName[i]);
  end;
  
  // Find conflicts (records overridden by other mods)
  ModInfo.Conflicts.Clear;
  // This would require scanning all records and checking for conflicts
  // Simplified version - in production you'd iterate through all records
  
  AddMessage('Exporting: ' + ModInfo.ModName);
end;

procedure WriteJsonOutput;
var
  JsonContent: string;
  i: integer;
begin
  JsonContent := '{' + sLineBreak;
  JsonContent := JsonContent + '  "mod_name": "' + ModInfo.ModName + '",' + sLineBreak;
  JsonContent := JsonContent + '  "file_name": "' + ModInfo.FileName + '",' + sLineBreak;
  JsonContent := JsonContent + '  "author": "' + ModInfo.Author + '",' + sLineBreak;
  JsonContent := JsonContent + '  "version": "' + ModInfo.Version + '",' + sLineBreak;
  
  // Masters
  JsonContent := JsonContent + '  "masters": [' + sLineBreak;
  for i := 0 to ModInfo.Masters.Count - 1 do
  begin
    JsonContent := JsonContent + '    "' + ModInfo.Masters[i] + '"';
    if i < ModInfo.Masters.Count - 1 then
      JsonContent := JsonContent + ',';
    JsonContent := JsonContent + sLineBreak;
  end;
  JsonContent := JsonContent + '  ],' + sLineBreak;
  
  // Conflicts (placeholder)
  JsonContent := JsonContent + '  "conflicts": [],' + sLineBreak;
  JsonContent := JsonContent + '  "exported_at": "' + DateTimeToStr(Now) + '"' + sLineBreak;
  JsonContent := JsonContent + '}' + sLineBreak;
  
  // Write to file
  OutputList.Text := JsonContent;
  OutputList.SaveToFile(OUTPUT_FILE);
  
  AddMessage('Export complete: ' + OUTPUT_FILE);
  AddMessage('Upload this file to SkyModderAI for analysis');
end;

function Process: integer;
var
  i: integer;
  File: IwbFile;
begin
  Result := 0;
  
  if wbFilesSelected.Count = 0 then
  begin
    AddMessage('No mod selected. Please select a mod to export.');
    Result := 1;
    Exit;
  end;
  
  // Export first selected mod
  File := wbFilesSelected[0];
  ExportMod(File);
  
  // Write JSON output
  WriteJsonOutput;
  
  // Instructions
  AddMessage('');
  AddMessage('=== SkyModderAI Export Complete ===');
  AddMessage('1. Go to https://skymodderai.com/mod-author/tools');
  AddMessage('2. Upload the generated JSON file');
  AddMessage('3. Get pre-release compatibility report');
end;

end.
