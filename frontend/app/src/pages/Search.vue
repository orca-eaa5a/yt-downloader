<template>
    <div class="full-screen">
        <div class="red-panel"></div>
        <div class="main-view">
            <div class="grid p-fluid w-100">
                <div class="col-12 md:col-8">
                    <div class="block w-100">
                        <VideoPlayer  ref="player" class="video-layout" style="padding: 0.5rem;"></VideoPlayer>
                        <div class="flex justify-content-between mb-2">
                            <p class="video-info video-title">{{this.video_info.title}}</p>
                            <p class="video-info video-length">{{this.video_info.length}}</p>
                        </div>
                        <p class="video-info video-url mb-3">
                            <a :href="this.video_info.url">{{this.video_info.url}}</a>
                        </p>
                        <div class="grid p-fluid w-100 justify-content-between">
                            <div class="col-12 md:col-6">
                                <Card>
                                    <template #title>
                                        <div class="w-100 flex justify-content-between">
                                            <span>구간 설정</span>
                                        </div>
                                    </template>
                                    <template #content>
                                        <div class="w-100 flex">
                                            <div class="grid p-fluid w-100">
                                                <div class="col-12 md:col-2 flex align-items-center">
                                                    <span class="video-length">재생지점</span>
                                                </div>
                                                <div class="col-12 md:col-7">
                                                    <InputText v-model="this.currentTime"/>
                                                </div>
                                                <div class="col-12 md:col-3"></div>
                                                
                                                <div class="col-12 md:col-2 flex align-items-center">
                                                    <span class="video-length">시작 점</span>
                                                </div>
                                                <div class="col-12 md:col-7">
                                                    <InputText v-model="this.trim.start"/>
                                                </div>
                                                <div class="col-12 md:col-2">
                                                    <Button class="p-button-raised p-button-rounded" label="재생" v-on:click="this.changeTimePoint(this.trim.start)"/>
                                                </div>
                                                <div class="col-12 md:col-2 flex align-items-center">
                                                    <span class="video-length">종료 점</span>
                                                </div>
                                                <div class="col-12 md:col-7">
                                                    <InputText v-model="this.trim.end"/>
                                                </div>
                                                <div class="col-12 md:col-2">
                                                    <Button class="p-button-raised p-button-rounded" label="재생" v-on:click="this.changeTimePoint(this.trim.end)"/>
                                                </div>
                                            </div>
                                        </div>
                                    </template>
                                </Card>
                            </div>
                            <div class="col-12 md:col-6">
                                <Card>
                                    <template #title>
                                        <div class="w-100 flex justify-content-between">
                                            <span>다운로드 요청</span>
                                            <Button class="btn-sm-red" icon="pi pi-download" label="다운로드" />
                                        </div>
                                    </template>
                                    <template #content>
                                        <div class="block">
                                            <div class="flex">
                                                <span style="font-size: 1.2rem;" class="mb-2">비디오 정보 : video/mp4</span>
                                            </div>
                                            <div class="flex">
                                                <span style="font-size: 1.2rem;" class="mb-4">재생 시간 : {{this.timestampToTime(this.timeStringToTimestamp(this.trim.end) - this.timeStringToTimestamp(this.trim.start))}}</span>
                                            </div>
                                            <div class="flex">
                                                <span style="font-size: 1rem;" class="mb-2">시작지점 : {{this.trim.start}}</span>
                                            </div>
                                            <div class="flex">
                                                <span style="font-size: 1rem;" class="mb-2">종료지점 : {{this.trim.end}}</span>
                                            </div>
                                        </div>
                                    </template>
                                </Card>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-12 md:col-4">
                    <div class="w-100 mb-4">
                        <Card style="margin: 0.5rem !important;">
                            <template #title>
                                <p class="card-header">타임스탬프</p>        
                            </template>
                            <template #content>
                                <div class="grid p-fluid m-0">
                                    <div class="w-100 flex mb-2" v-for="item of this.video_info.time_info" :key="item">
                                        <span style="width: 20%;">
                                            <Button class="btn-empty" :value="item.timestamp" v-on:click="this.changeTimePoint(item.timestamp)">{{item.timestamp}}</Button>
                                        </span>
                                        <span style="width: 80%; text-align:left; ">{{item.tag}}</span>
                                    </div>
                                </div>
                            </template>
                            <template #footer>
                                <Button class="btn-sm-red" icon="pi pi-search" label="좀 더 확인하기" />
                            </template>
                        </Card>
                    </div>
                    <div class="w-100">
                        <Card style="margin: 0.5rem !important;">
                            <template #title>
                                <p class="card-header">다운로드 가능 목록</p>        
                            </template>
                            <template #content>
                                <div class="grid p-fluid m-0">
                                    <div class="w-100 flex mb-2 border-box" v-for="item of this.vStreams" :key="item">
                                        <span style="width: 38%;">{{item.mime_type}}</span>
                                        <span style="width: 37%;">{{item.quality}}</span>
                                        <span style="width: 25%;">
                                            <Button class="p-button-primary" label="선택" url="{{item.url}}" v-on:click="setupVideoPlayer(item.url, item.mime_type)"></Button>
                                        </span>
                                    </div>
                                </div>
                            </template>
                            <template #footer>
                                <Button class="btn-sm-red" icon="pi pi-bars" label="고화질 다운로드" v-on:click="this.openDownloadModal"/>
                            </template>
                        </Card>
                    </div>
                </div>
            </div>
            
            <Dialog header="Header" :visible="downloadModalVisible" >
                <p class="m-0">test</p>
                <template #footer>
                    <Button class="btn-sm-red" icon="pi pi-bars" label="취소" v-on:click="this.closeDownloadModal"/>
                </template>
            </Dialog>
        </div>
        <div class="black-panel"></div>
    </div>
</template>

<script>
import VideoPlayer from '@/components/Video.vue';
export default {
    components:{
        VideoPlayer
    },
    data(){
        return{
            video_source: '',
            video_type: '',
            video_info:{
                title: '',
                url: '',
                length: '',
                time_info: [],
            },
            vStreams: [],
            currentTime: 0,
            trim:{
                start: '00:00:00',
                end: '00:00:00',
            },
            downloadModalVisible: false,
            selectedVideoType: '',

        }
    },
    methods:{
        openDownloadModal() {
            this.downloadModalVisible = true;
        },
        closeDownloadModal() {
            this.downloadModalVisible = false;
        },
        timeStringToTimestamp(s){
            let time = s;
            let array = time.split(":");
            let timestamp = 0.0;
            if(array.length === 2){
                timestamp = (parseInt(array[0], 10) * 60) + parseFloat(array[1]);
            }
            else if (array.length === 3){
                timestamp = (parseInt(array[0], 10) * 60 * 60) + (parseInt(array[1], 10) * 60) + parseFloat(array[2]);
            }
            else{
                timestamp = NaN;
            }
            return timestamp
        },
        timestampToTime(ts){
            return new Date(ts * 1000).toISOString().slice(11, 23);
        },
        playVideo(){
            this.$refs.player.player.play();
        },
        changeTimePoint(s){
            let ts = this.timeStringToTimestamp(s);
            this.$refs.player.setCurrentTime(ts)
            this.playVideo();
        },
        setupVideoPlayer(url, type){
            this.$refs.player.setVideoPlayer(url, type);
            this.trim.start = this.timestampToTime(0);
            this.$refs.player.addVideoEventListener("loadedmetadata", () => {
                this.trim.end = this.timestampToTime(this.$refs.player.videoElem.duration);
                this.video_info.length = this.trim.end;
            });
            this.$refs.player.addVideoEventListener("timeupdate", () => {
                this.currentTime = this.timestampToTime(this.$refs.player.getCurrentTime());
            });
        },
        async initVideoPlayer(){
            let resp = await fetch(this.url + "/vidinfo");
            if(resp.status === 200){
                let json = await resp.json();
                if(json.success === true){
                    let data = json.data;
                    this.video_info.time_info = data.time_info;
                    this.video_info.length = data['length'];
                    this.video_info.title = data.title;
                    this.vStreams = data.streams;
                    this.video_source = this.vStreams[this.vStreams.length-1].url;
                    this.video_type = this.vStreams[this.vStreams.length-1].mime_type;
                    this.setupVideoPlayer(this.video_source, this.video_type);
                    return;
                }
            }
            alert('비디오 정보 조회에 실패했습니다.');
            throw new Error('fail to get video information')
        }
    },
    computed: {
        
    },
    async mounted(){
        this.initVideoPlayer();
    }
    
}
</script>
<style scoped lang="scss">
@import "../assets/css/main.css";
@import url('https://fonts.googleapis.com/css2?family=Heebo&family=Poppins:wght@300&family=Rubik&display=swap');

@media only screen and (max-width: 440px) {
    .main-view { 
        padding: .5rem .7rem !important;
    }
    .border-box span{
        font-size: 1rem !important;
    }
}
//override
.grid {
    margin: 0px;
}
.red-panel{
    background-color: rgb(254, 114, 114);
    width: 100vw;
    height: 60px;
}
.black-panel{
    background-color: rgb(92, 92, 92);
    width: 100vw;
    height: 60px;
}
.main-view{
    padding: 3rem 5rem;
    height: calc(100vh - 120px);
}
.video-layout{
    max-width: 100%;
    min-width: 70%;
    max-height: 100%;
    min-height: 40%;
    border-radius: 20px;
    overflow: hidden;
}

.video-info{
    text-align: left;
    font-family: 'Heebo', sans-serif;
    margin: 0;
    color: black;
    font-weight: 600;
}

.video-title{
    font-size: 1.7rem;
}

.video-url{
    font-size: .9rem;
    color: rgb(44, 125, 255);
}

.video-length{
    display: flex;
    align-items: center;
    font-size: 1.2rem;
    color: #626262;
}

.card-header{
    text-align: left;
    font-family: 'Heebo', sans-serif;
    margin: 0px 0px 0.2rem 0px;
    color: rgb(254, 114, 114);
    font-weight: 600;
    font-size: 1.5rem;
    padding: 0;
}

.border-box{
    border: 0.1rem solid rgb(134, 134, 134);
    border-radius: 10px;
    overflow: hidden;
    display: flex;
    justify-content: center;
}

.border-box span{
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
}

.border-box button{
    border-top-left-radius: 0px !important;
    border-bottom-left-radius: 0px !important;
}

//override
.p-card{
    border-radius: 0px !important;
}

.btn-sm-red{
    width: 11rem !important;
    background-color: rgb(254, 114, 114);
    border: 0.1rem solid rgb(255, 119, 119);
}

.btn-empty{
    background-color: initial !important;
    text-align:left; color: rgb(44, 125, 255);
    padding: 0 !important;
    border: none !important;
}
</style>
<style>
.p-dialog{
    border: 0.12rem solid rgb(134, 134, 134);
    box-shadow: none;
}

.p-dialog .p-dialog-header{
    color: rgb(254, 114, 114) !important;
}

.p-dialog .p-dialog-header .p-dialog-header-icon{
    display: none;
}
</style>