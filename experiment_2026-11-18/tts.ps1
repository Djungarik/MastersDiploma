Add-Type -AssemblyName System.Speech
$scenes = Get-Content -Raw -Encoding UTF8 scenes.json | ConvertFrom-Json
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(48000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
"voice: " + $synth.Voice.Name
foreach ($s in $scenes) {
  $path = Join-Path (Get-Location) ("wav\scene{0:d2}.wav" -f $s.id)
  $synth.SetOutputToWaveFile($path, $fmt)
  $synth.Speak($s.text)
}
$synth.SetOutputToNull()
