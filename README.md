# <img src='https://0000.us/klatchat/app/files/neon_images/icons/neon_skill.png' card_color="#FF8600" width="50" style="vertical-align:bottom">Device Control Center

## Summary

Handles system-wide settings and controls.

## Requirements

No special required packages for this skill.

## Description

Device Control skill handles base core/OS controls and interactions It is responsible for:

-   Changing dialog modes;
    
-   Clearing recorded likes, audio, selected and full text transcriptions, and the rest of the user’s data;
    
-   Audible commands to switch between skipping and requiring wake words in two modes: dev and user;

-   Shutting down the whole device;
    
-   Exiting from Neon’s process;

  

## Examples

First, make your request. Say `“Hey Neon”` if you are in the wake words mode. Then say your desired command. Use the following list as a reference:

- "Change your dialog mode to (random/default)"
- "clear my user (profile/transcripts/likes/media/preferences/languages)"
- "skip wake words"
- "require wake words"
- "I want you to exit"
- "I want you to shutdown"
- "I want you to restart"

## Change dialog mode

I want you to begin {dialogmode} (dialog|dialogue) mode  
Change your (dialog|dialogue) mode to {dialogmode}

  

Where *dialog mode* is one of the following:

-   random
    
-   default
    
-   primary
    
-   normal
    

## Clear variety of recorded data

    I want to clear my user *data option*
    
    neon clear my user *data option*
    
    erase all of my user *data option*

  

where *data option* is one of the following:

-   data
    
-   transcripts
    
-   selected transcriptions
    
-   like
    
-   brands
    
-   ignored brands
    
-   pictures and videos
    
-   media
    
-   preferences
    
-   languages
    
-   cached responses
    
-   profile
    

## Switch between skipping and requiring wake words

If you are in devMode, your commands are limited to the following in order to avoid false-positives:

    -   require {ww}
        
    -   quit skipping {ww}
    

  

and

  

    -   skip {ww}
        
    -   begin skipping {ww}
        

  

where *{ww}* stands for wake words.

If you are in user mode, you can use the following commands to use wakewords:

    -   solo mode
        
    -   I am in (a group |group)
        
    -   I am not alone
        
    -   use {ww}
        
    -   require {ww}
        
    -   begin requiring {ww}
        
    -   stop (skipping {ww} |solo mode )
        
    -   end (skipping {ww} |solo mode )
        
    -   deny (skipping {ww} |solo mode )
        
    -   quit (skipping {ww} |solo mode )
    

  

And the following to start skipping the wakewords:

    -   I am alone
        
    -   skip {ww}
        
    -   start ( skipping {ww} | solo mode )
        
    -   begin ( skipping {ww} | solo mode )
        
    -   allow ( skipping {ww} | solo mode )
        
    -   enter ( skipping {ww} | solo mode )

Most likely, Neon will ask for the confirmation to most of the choices available above. Follow the prompts and reply 
either with simple positive or negative answer, or follow it up by the requested 3-digit code.

Wait for the successful confirmation or action execution from Neon. Most commands should be instantaneous.

## Location

    ${skills}/device-control-center.neon

## Files
<details>
<summary>Click to expand.</summary>
<br>

    ${skills}/device-control-center.neon/__init__.py  
    ${skills}/device-control-center.neon/test  
    ${skills}/device-control-center.neon/test/intent  
    ${skills}/device-control-center.neon/test/intent/StopSkippingWakeWords.intent.json  
    ${skills}/device-control-center.neon/test/intent/StartSkippingWakeWords.intent.json  
    ${skills}/device-control-center.neon/test/intent/updateNeon.intent.json  
    ${skills}/device-control-center.neon/test/intent/DevStopSkippingWakeWords.intent.json  
    ${skills}/device-control-center.neon/test/intent/DevStartSkippingWakeWords.intent.json  
    ${skills}/device-control-center.neon/test/intent/exit_shutdown.json  
    ${skills}/device-control-center.neon/test/intent/ChangeDialogOptions.intent.json  
    ${skills}/device-control-center.neon/settings.json  
    ${skills}/device-control-center.neon/vocab  
    ${skills}/device-control-center.neon/vocab/en-us  
    ${skills}/device-control-center.neon/vocab/en-us/show_demo.intent  
    ${skills}/device-control-center.neon/vocab/en-us/dev_skip_ww_finish.intent  
    ${skills}/device-control-center.neon/vocab/en-us/exit_shutdown.intent  
    ${skills}/device-control-center.neon/vocab/en-us/change_dialog.intent  
    ${skills}/device-control-center.neon/vocab/en-us/random_number.entity  
    ${skills}/device-control-center.neon/vocab/en-us/dev_skip_ww_start.intent  
    ${skills}/device-control-center.neon/vocab/en-us/clear_user_data.intent  
    ${skills}/device-control-center.neon/vocab/en-us/neon.voc  
    ${skills}/device-control-center.neon/vocab/en-us/dialogmode.entity  
    ${skills}/device-control-center.neon/vocab/en-us/ww.entity  
    ${skills}/device-control-center.neon/vocab/en-us/update_neon.voc  
    ${skills}/device-control-center.neon/vocab/en-us/confirm_no.voc  
    ${skills}/device-control-center.neon/vocab/en-us/confirm_yes.voc  
    ${skills}/device-control-center.neon/vocab/en-us/skip_ww_start.intent  
    ${skills}/device-control-center.neon/vocab/en-us/confirm_numeric.intent  
    ${skills}/device-control-center.neon/vocab/en-us/skip_ww_finish.intent  
    ${skills}/device-control-center.neon/README.md
</details>

## Class Diagram

[Click Here](https://0000.us/klatchat/app/files/neon_images/class_diagrams/device-control-center.png)

## Available Intents
<details>
<summary>Click to expand.</summary>
<br>

### show_demo.intent

    neon i want to see demo  
    neon show me the demo

  

### dev_skip_ww_finish.intent

    require {ww}  
    quit skipping {ww}

  

### exit_shutdown.intent

    i want you to (exit|shutdown|shut down)

### change_dialog.intent

    switch to (the|) {dialogmode} (dialog|dialogue) mode  
    i want you to begin {dialogmode} (dialog|dialogue) mode  
    change your (dialog|dialogue) mode to {dialogmode}  
    change your (dialog|dialogue) mode

### random_number.entity

    ###  
    # # #

  

### dev_skip_ww_start.intent

    skip {ww}  
    begin skipping {ww}

  

### clear_user_data.intent

    clear my user data  
    clear all of my user data  
    erase my user data  
    erase all of my user data  
    i want to clear my user selected transcriptions  
    i want to clear my user selected transcripts  
    i want to clear my user selected transcript  
    i want to clear my user ignored brands  
    i want to clear my user ignored brands  
    i want to clear my user transcripts  
    i want to clear my user transcript  
    i want to clear my user likes  
    i want to clear my user like  
    i want to clear my user brands  
    i want to clear my user brand  
    i want to clear my user data  
    i want to erase my user selected transcriptions  
    i want to erase my user selected transcripts  
    i want to erase my user selected transcript  
    i want to erase my user ignored brands  
    i want to erase my user ignored brand  
    i want to erase my user transcripts  
    i want to erase my user transcript  
    i want to erase my user likes  
    i want to erase my user like  
    i want to erase my user brands  
    i want to erase my user brand  
    i want to erase my user pictures and videos  
    i want to erase my user media  
    i want to erase my user preferences  
    i want to erase my user languages  
    i want to erase my user cached responses  
    i want to erase my user profile  
    neon clear my user selected transcriptions  
    neon clear my user selected transcripts  
    neon clear my user selected transcript  
    neon clear my user ignored brands  
    neon clear my user ignored brand  
    neon clear my user transcripts  
    neon clear my user transcript  
    neon clear my user likes  
    neon clear my user like  
    neon clear my user brands  
    neon clear my user brand  
    neon clear my user data  
    neon erase my user selected transcriptions  
    neon erase my user selected transcripts  
    neon erase my user selected transcript  
    neon erase my user ignored brands  
    neon erase my user ignored brand  
    neon erase my user transcripts  
    neon erase my user transcript  
    neon erase my user likes  
    neon erase my user like  
    neon erase my user brands  
    neon erase my user brand  
    neon erase my user pictures and videos  
    neon erase my user media  
    neon erase my user preferences  
    neon erase my user languages  
    neon erase my user cached responses  
    neon erase my user profile

### neon.voc

    neon  
    leon  
    nyan

### dialogmode.entity

    random  
    default  
    primary  
    normal

### ww.entity

    wake words  
    awake words  
    weight words  
    wakewords  
    awakewords  
    weightwords

  

### update_neon.voc

    update my neon device  
    update my device software  
    check for updates

  

### confirm_no.voc

    no  
    stop  
    break  
    exit  
    quit  
    end  
    nevermind  
    cancel  
    never mind

### confirm_yes.voc

    yes  
    continue  
    go ahead  
    begin  
    start

### skip_ww_start.intent

    i am alone  
    skip {ww}  
    start ( skipping {ww} | solo mode )  
    begin ( skipping {ww} | solo mode )  
    allow ( skipping {ww} | solo mode )  
    enter ( skipping {ww} | solo mode )  
    and her ( skipping {ww} | solo mode )

### confirm_numeric.intent

    go ahead {random_number}

  

### skip_ww_finish.intent

    solo mode  
    i am in (a group |group)  
    i am not alone  
    use {ww}  
    require {ww}  
    begin requiring {ww}  
    stop (skipping {ww} |solo mode )  
    end (skipping {ww} |solo mode )  
    deny (skipping {ww} |solo mode )  
    quit (skipping {ww} |solo mode )

 </details>

## Details

### Text

        Neon, begin skipping wake words
        >> Should I start skipping wake words?
        Yes
        >> Okay, Starting to skip wake words.
    
        Require wake words.
        >> Should I start requiring wake words?
        Yes
        >> Okay, entering wake words mode.

Please refer to [How to Use](how-to-use) for more information.

### Picture

### Video

## Contact Support

Use the [link](https://neongecko.com/ContactUs) or [submit an issue on GitHub](https://help.github.com/en/articles/creating-an-issue)

## Credits

@NeonGeckoCom
@reginaneon
@NeonDaniel

## Category
**Configuration**
Daily

## Tags
#NeonGecko
#NeonAI
#controls
#device
#wake words
#power
#settings




