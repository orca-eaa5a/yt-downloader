<template>
    <div>
        <video controls ref="videoPlayer" class="video-js vjs-default-skin vjs-big-play-centered">
            <source id='player-src'
            :src="this.source"
            :type="this.type"
            >
        </video>
    </div>
</template>

<script>
import videojs from 'video.js';

export default {
    name: 'VideoPlayer',
    props: {
        options: {
            type: Object,
            default() {
            return {};
            }
        },
    },
    data() {
        return {
            player: null,
            videoElem:null,
            duration:0,
            source:null,
            type:null
        }
    },
    mounted() {
        
    },
    methods:{
        setVideoPlayer(source, type){
            this.videoElem = this.$refs.videoPlayer;
            this.source = source;
            this.type = type;
            
            let srctag = document.querySelector('#player-src');
            srctag.setAttribute('src', this.source);
            srctag.setAttribute('type', this.type)

            this.player = videojs(this.videoElem, this.options, () => {
                console.log('video is ready');
                this.player.log('onPlayerReady', this);
                this.player.fluid(true);
                this.player.load();
            });

            // this.player.src(
            //     {src:this.source, type:this.type}
            // )
            // this.player.src(
            //     {src:this.source, type:this.type}
            // )
            // this.player.load();
            // this.player.fluid(true);
            this.videoElem.addEventListener("loadedmetadata", () => {
                // console.log(videoElem.duration);
                this.duration = this.videoElem.duration;
            });
        },
        addVideoEventListener(evt, cb){
            this.videoElem.addEventListener(evt, cb)
        },
        getDuration(){
            return this.duration;
        },
        getCurrentTime(){
            return this.player.currentTime();
        },
        setCurrentTime(timestamp){
            this.player.pause();
            this.player.currentTime(timestamp);
        },
    },
    beforeDestroy() {
        if (this.player) {
            this.player.dispose();
        }
    }

}
</script>

<style type="text/css">
.video-js.video-js .vjs-big-play-button {
    opacity: .7;
    width: 60px;
    height: 60px;
    top: 0px;
    left: 0px;
    right: 0px;
    bottom: 0px;
    margin: auto;
    border-radius: 90px;
    border-style: solid;
    border-width: 2px;
    border-color: #FFFFFF;
    font-size: 2.4rem;
    text-align: center;
}

.video-js .vjs-time-control {
    display: block !important;
}
.vjs-remaining-time {
    display: none !important;
}
</style>

<style scoped lang='scss'>

</style>