DGPlayer
========

### Interface
```java
interface DGPlayer {
    on(event, callback);           // event: play, pause, volume 
    off(event, callback);
    
    property string state;          // buffering, playing, or paused
    property number bufferProgress; // 0-100
    property number startTime;      // in milliseconds since the epoch
    property url coverArt;
    property number volume;         // 0-100
    property string songTitle;
    property string songArtist;
}
```