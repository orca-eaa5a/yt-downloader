<template>
    <div class="full-screen">
        <div class="flex red-panel justify-content-end align-items-center">
            <Button label="메인으로" class="p-button-danger signup-button" v-on:click="this.gotoMain()"/>
        </div>
        <div class="main-view">
            <div class="grid p-fluid w-100">
                <div class="col-12 md:col-8">
                    <div class="block w-100">
                        <div class="grid w-100">
                            <div class="col-12 md:col-12">
                                <VideoPlayer  ref="player" class="video-layout"></VideoPlayer>
                                <div class="response-flex justify-content-between mb-2 mt-2">
                                    <p class="video-info video-title">{{this.video_info.title}}</p>
                                    <p class="video-info video-length">{{this.video_info.length}}</p>
                                </div>
                                <p class="video-info video-url mb-3">
                                    <a :href="this.video_info.url">{{this.video_info.url}}</a>
                                </p>
                            </div>
                        </div>
                        <div class="grid p-fluid w-100 justify-content-between">
                            <div class="col-12 md:col-8">
                                <Card>
                                    <template #title>
                                        <div class="w-100 flex justify-content-between">
                                            <span>구간 설정</span>
                                            <SelectButton v-model="selectedEditTimestamp" :options="this.tpOptions" optionLabel="name" optionValue="value" aria-labelledby="single"/>
                                        </div>
                                    </template>
                                    <template #content>
                                        <div class="w-100 block">
                                            <div class="field-radiobutton">
                                                <span class="video-length">현재지점</span>
                                                <InputText v-model="this.currentTime" class="timestamp-text"/>
                                            </div>
                                            
                                            <div class="field-radiobutton">
                                                <span class="video-length">시작점</span>
                                                <InputText v-model="this.trim.start" class="timestamp-text" :class="{'p-invalid' : !this.timestampInputValidation(this.trim.start)}"/>
                                            </div>
                                            <div class="field-radiobutton">
                                                <span class="video-length">종료점</span>
                                                <InputText v-model="this.trim.end" class="timestamp-text" :class="{'p-invalid' : !this.timestampInputValidation(this.trim.end)}"/>
                                            </div>
                                            <div class="w-100 flex justify-content-center mt-1">
                                                <Button class="mr-1 timestamp-ctrl-btn p-button-raised p-button-rounded" label="재생" v-on:click="this.changeTimePoint(this.trim[this.selectedEditTimestamp])"/>
                                                <Button class="mr-1 timestamp-ctrl-btn p-button-raised p-button-rounded" label="중지" v-on:click="this.pauseVideo()"/>
                                                <Button class="mr-1 timestamp-ctrl-btn p-button-raised p-button-rounded" label="선택" v-on:click="this.syncTimepoint(this.trim, this.selectedEditTimestamp)"/>
                                                <Button class="mr-1 timestamp-ctrl-btn p-button-raised p-button-rounded" label="+0.1s" v-on:click="this.addMs(this.trim, this.selectedEditTimestamp)"/>
                                                <Button class="timestamp-ctrl-btn p-button-raised p-button-rounded" label="-0.1s" v-on:click="this.subMs(this.trim, this.selectedEditTimestamp)"/>
                                            </div>
                                        </div>
                                    </template>
                                </Card>
                            </div>
                            <div class="col-12 md:col-4">
                                <Card>
                                    <template #title>
                                        <div class="w-100 flex justify-content-between">
                                            <span>다운로드 요청</span>
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
                                    <template #footer>
                                        <Button class="btn-sm-red" icon="pi pi-download" label="다운로드" v-on:click="this.download_request()"/>
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
                                <Button class="btn-sm-red" icon="pi pi-search" label="좀 더 확인하기" v-on:click="this.load_timestamp_advanced()" />
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
        
            <Dialog header="다운로드" :visible="progressModalVisible" :breakpoints="{'960px': '75vw', '640px': '90vw'}" :style="{width: '20vw'}" :modal="true" contentClass="flex justify-content-center">
                <div>
                    <ProgressSpinner/>
                    <p style="text-align: center">{{this.progressMessage}}</p>
                </div>
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
            requestedVideo: '',
            video_source: '',
            video_type: '',
            video_info:{
                title: '',
                url: '',
                length: '',
                time_info: [],
            },
            selectedEditTimestamp: null,
            vStreams: [],
            currentTime: 0,
            trim:{
                start: '00:00:00',
                end: '00:00:00',
            },
            downloadModalVisible: false,
            progressModalVisible: false,
            progressMessage:'',
            selectedVideoType: '',
            tpOptions:[
                {name: '시작지점', value:'start'},
                {name: '종료지점', value:'end'},
            ]

        }
    },
    methods:{
        js_sleep(ms) {
            return new Promise((resolve) => setTimeout(resolve, ms))
        },
        timestampInputValidation(val){
            const regex = /([0-9]+:)?[0-5]?[0-9]:[0-5][0-9](\.[0-9]{1,3})?$/;
            return regex.test(val);
        },
        gotoMain(){
            this.$router.push('/');
        },
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
        pauseVideo(){
            this.$refs.player.player.pause();
        },
        syncTimepoint(tr, obj_n){
            if(!obj_n){
                alert('동기화할 시작점 또는 종료점을 선택해주세요.');
            }
            else{
                tr[obj_n] = this.currentTime;
            }
        },
        
        changeTimePoint(s){
            let ts = '';
            if(!s){
                s = this.currentTime;
            }
            ts = this.timeStringToTimestamp(s);
            this.$refs.player.setCurrentTime(ts);
            this.playVideo();
        },
        addMs(tr, obj_n){
            let s = tr[obj_n]
            let ts = this.timeStringToTimestamp(s);
            ts+=0.1
            tr[obj_n] = this.timestampToTime(ts);
        },
        subMs(tr, obj_n){
            let s = tr[obj_n]
            let ts = this.timeStringToTimestamp(s);
            ts-=0.1
            if(ts<0){
                tr[obj_n] = this.timestampToTime(0);    
            }
            else{
                tr[obj_n] = this.timestampToTime(ts);
            }
        },
        setupVideoPlayer(url, type){
            this.$refs.player.setVideoPlayer(url, type);
            this.trim.start = this.timestampToTime(0);
            this.$refs.player.player.on("loadedmetadata", () => {
                this.trim.end = this.timestampToTime(this.$refs.player.videoElem.duration);
                this.video_info.length = this.trim.end;
            });
            this.$refs.player.player.on("timeupdate", () => {
                this.currentTime = this.timestampToTime(this.$refs.player.getCurrentTime());
            });
        },
        full_download(video_url){
            video_url = "https://"+video_url;
            fetch(video_url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/mp4',
                },
            })
            .then((response) => response.blob())
            .then((blob) => {
                const url = window.URL.createObjectURL(
                    new Blob([blob]),
                );
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute(
                    'download',
                    this.video_info.title+".mp4",
                );
                document.body.appendChild(link);
                link.click();
                link.parentNode.removeChild(link);
            });
        },
        async trim_process_healthcheck(ticket){
            let aws_api = this.api_url + "/healthcheck";
            let resp = await fetch(aws_api, {
                method: "POST",
                headers:{
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    data:{
                        ticket:ticket
                    }
                })
            });
            let data = await resp.json();
            if(data.statusCode === 200 && data.body.success){
                data = data.body.data
                if('status' in data){
                    if(data.status === 'RUNNING'){
                        return undefined;
                    }
                    else if(data.status === 'SUCCEEDED'){
                        return data;
                    }
                    else{
                        alert("trimming process is failed with error " + data.err)
                        throw new Error("trimming process is failed with error " + data.err);
                    }
                }
                else{
                    console.log(data);
                    throw new Error("invalid response");
                }
            }
        },
        async trim_request(){
            let aws_api = this.api_url + "/trim-request";
            //먼저 trim을 요청하는 API는 동기적으로 동작
            //-> trim이 제대로 요청되었는지 확인 필요!
            this.progressModalVisible = true;
            this.progressMessage = "자르기 요청 시작";
            let resp = await fetch(aws_api, {
                method: "POST",
                headers:{
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    o_url:this.video_info.url,
                    url:this.video_source,
                    sp:this.trim.start,
                    ep:this.trim.end,
                    m_duration:parseInt(this.timeStringToTimestamp(this.video_info.length))
                })
            });
            resp = await resp.json();
            if(resp.statusCode === 200 && resp.body.success){
                this.progressMessage = "자르기 요청 성공";
                let data = resp.body.data;
                if('ticket' in data){
                    let healthcheck_cnt = 0;
                    while(healthcheck_cnt <= 5){
                        let status = await this.trim_process_healthcheck(data.ticket);
                        this.progressMessage = "진행상태 체크 : " + String(healthcheck_cnt);
                        if(status){
                            console.log('trimming process is succeed!');
                            this.progressMessage = "요청 완료";
                            this.progressMessage = "다운로드 시작";
                            this.full_download(status.url);
                            this.progressMessage = "다운로드 완료";
                            break
                        }
                        else{
                            healthcheck_cnt += 1;
                            await this.js_sleep(2000);
                        }
                    }
                    if(healthcheck_cnt>5){
                        this.progressMessage = "요청 실패 : 타임아웃";
                        alert("trimming process timeout.. data: " + JSON.stringify(data));
                    }
                }
                else if('url' in data){
                    this.progressMessage = "캐시 다운로드";
                    this.full_download(data.url);
                    this.progressMessage = "다운로드 완료";
                }
                else{
                    this.progressMessage = "요청 실패 : 서버 오류";
                    alert("trimming process is failed.. data: " + JSON.stringify(data));
                }
            }
            else{
                this.progressMessage = "요청 실패 : 요청 값을 확인하세요";
                alert("trimming process is failed.. resp: " + JSON.stringify(resp));
            }
            this.progressModalVisible = false;
        },
        async download_request(){
            let duration = this.timeStringToTimestamp(this.video_info.length);
            let ep = this.timeStringToTimestamp(this.trim.end);
            let sp = this.timeStringToTimestamp(this.trim.start);

            if((duration !== ep) || (sp !== 0)){
                this.trim_request();
            }
            else{
                this.full_download(this.video_source);
            }
        },
        async load_timestamp_advanced(){
            let aws_api = this.api_url + "/timestamp";
            let resp = await fetch(aws_api + "?url=" + this.video_info.url);
            resp = await resp.json();
            if(resp.statusCode === 200 && resp.body.success){
                let data = resp.body.data;
                this.video_info.time_info = data;
            }
            else{
                alert('fail to crawal timestamp information : '+JSON.stringify(resp));
            }
        },
        async initVideoPlayer(){
            let resp = await fetch(this.api_url + "/query?q="+this.requestedVideo);
            if(resp.status === 200){
                let json = await resp.json();
                if(json.body.success === true){
                    let data = json.body.data;
                    this.video_info.time_info = data.time_info;
                    this.video_info.length = data['length'];
                    this.video_info.title = data.title;
                    this.video_info.url="https://www.youtube.com/watch?v="+data.vid;
                    this.vStreams = data.streams;
                    this.video_source = this.vStreams[this.vStreams.length-1].url;
                    this.video_type = this.vStreams[this.vStreams.length-1].mime_type;
                    this.setupVideoPlayer(this.video_source, this.video_type);
                    return;
                }
                else{
                    console.log(json);
                    alert('비디오 정보 조회에 실패했습니다.');
                    throw new Error('fail to get video information')
                }
            }
            else{
                console.log(resp);
                alert('비디오 정보 요청에 실패했습니다.');
                throw new Error('fail to request api get video information ')
            }
        }
    },
    computed: {
        
    },
    watch: {

    },
    async mounted(){
        document.body.style.zoom = "75%";
        console.log(this.$route.query.q);
        this.requestedVideo = this.$route.query.q
        if(!this.requestedVideo){
            alert('Youtube 비디오 URL 또는 Video ID를 입력 해주세요!');
            this.gotoMain();
        }

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
    .video-length{
        font-size: .9rem !important;
    }
    .black-panel{
        height: 0px !important;
    }
    .main-view{
        height: calc(100% - 60px) !important;
    }
    .timestamp-ctrl-btn{
        padding: 0.5rem 0.1rem !important;
    }
    .response-flex{
        display: block !important;
    }
}
@media only screen and (min-width: 800px) {
    .timestamp-ctrl-btn{
        padding: 0.5rem 1rem !important;
    }
    .response-flex{
        display: flex !important;
    }
}

//override
html{
    font-size: 12px;
}
.grid {
    margin: 0px;
}
.red-panel{
    background-color: rgb(254, 114, 114);
    width: 100%;
    height: 60px;
}
.black-panel{
    background-color: rgb(92, 92, 92);
    width: 100%;
    height: 60px;
}
.main-view{
    padding: 2rem 12rem;
    height: calc(100% - 120px);
    overflow-y: auto;
    overflow-x: scroll;
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
    width: 20%;
    color: #626262;
}

.timestamp-text{
    width:60% !important;
    margin-right: 1.0rem;
}

.timestamp-ctrl-btn{
    width:65px !important;
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

.signup-button{
    padding: 10px !important;
    margin: 15px 30px 15px 15px !important;
    min-width: 100px !important;
    border-radius: 20px !important;
}

</style>