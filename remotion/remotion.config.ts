import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
// H.264 + yuv420p so the mp4 plays everywhere (Safari/iOS/QQ/WeChat in-app browsers).
Config.setCodec('h264');
Config.setPixelFormat('yuv420p');
