import os
import os.path as osp
import torch
import torchaudio
from pytorch_fid.fid_score import calculate_frechet_distance
from torch import distributed
from tqdm import tqdm
from transformers import Wav2Vec2ForCTC
import torch.nn.functional as F
import numpy as np

import trainer.eval.evaluator as evaluator
from data.audio.paired_voice_audio_dataset import load_tsv_aligned_codes
from data.audio.unsupervised_audio_dataset import load_audio
from models.clip.mel_text_clip import MelTextCLIP
from models.audio.tts.tacotron2 import text_to_sequence
from scripts.audio.gen.speech_synthesis_utils import load_discrete_vocoder_diffuser, wav_to_mel, load_speech_dvae, \
    convert_mel_to_codes, load_univnet_vocoder, wav_to_univnet_mel
from trainer.injectors.audio_injectors import denormalize_tacotron_mel
from utils.util import ceil_multiple, opt_get


class AudioDiffusionFid(evaluator.Evaluator):
    """
    Evaluator produces generate from a diffusion model, then uses a CLIP model to judge the similarity between text & speech.
    """
    def __init__(self, model, opt_eval, env):
        super().__init__(model, opt_eval, env, uses_all_ddp=True)
        self.real_path = opt_eval['eval_tsv']
        self.data = load_tsv_aligned_codes(self.real_path)
        if distributed.is_initialized() and distributed.get_world_size() > 1:
            self.skip = distributed.get_world_size()  # One batch element per GPU.
        else:
            self.skip = 1
        diffusion_steps = opt_get(opt_eval, ['diffusion_steps'], 50)
        diffusion_schedule = opt_get(env['opt'], ['steps', 'generator', 'injectors', 'diffusion', 'beta_schedule', 'schedule_name'], None)
        if diffusion_schedule is None:
            print("Unable to infer diffusion schedule from master options. Getting it from eval (or guessing).")
            diffusion_schedule = opt_get(opt_eval, ['diffusion_schedule'], 'cosine')
        conditioning_free_diffusion_enabled = opt_get(opt_eval, ['conditioning_free'], False)
        conditioning_free_k = opt_get(opt_eval, ['conditioning_free_k'], 1)
        self.diffuser = load_discrete_vocoder_diffuser(desired_diffusion_steps=diffusion_steps, schedule=diffusion_schedule,
                                                       enable_conditioning_free_guidance=conditioning_free_diffusion_enabled,
                                                       conditioning_free_k=conditioning_free_k)
        self.dev = self.env['device']
        mode = opt_get(opt_eval, ['diffusion_type'], 'tts')
        self.local_modules = {}
        if mode == 'tts':
            self.diffusion_fn = self.perform_diffusion_tts
        elif mode == 'original_vocoder':
            self.local_modules['dvae'] = load_speech_dvae().cpu()
            self.diffusion_fn = self.perform_original_diffusion_vocoder
        elif mode == 'vocoder':
            self.local_modules['dvae'] = load_speech_dvae().cpu()
            self.diffusion_fn = self.perform_diffusion_vocoder
        elif mode == 'tts9_mel':
            mel_means, self.mel_max, self.mel_min, mel_stds, mel_vars = torch.load('../experiments/univnet_mel_norms.pth')
            self.local_modules['dvae'] = load_speech_dvae().cpu()
            self.local_modules['vocoder'] = load_univnet_vocoder().cpu()
            self.diffusion_fn = self.perform_diffusion_tts9_mel_from_codes

    def perform_diffusion_tts(self, audio, codes, text, sample_rate=5500):
        real_resampled = torchaudio.functional.resample(audio, 22050, sample_rate).unsqueeze(0)
        aligned_codes_compression_factor = sample_rate * 221 // 11025
        output_size = codes.shape[-1]*aligned_codes_compression_factor
        padded_size = ceil_multiple(output_size, 2048)
        padding_added = padded_size - output_size
        padding_needed_for_codes = padding_added // aligned_codes_compression_factor
        if padding_needed_for_codes > 0:
            codes = F.pad(codes, (0, padding_needed_for_codes))
        output_shape = (1, 1, padded_size)
        gen = self.diffuser.p_sample_loop(self.model, output_shape,
                                    model_kwargs={'tokens': codes.unsqueeze(0),
                                                  'conditioning_input': real_resampled})
        return gen, real_resampled, sample_rate

    def perform_original_diffusion_vocoder(self, audio, codes, text, sample_rate=11025):
        mel = wav_to_mel(audio)
        mel_codes = convert_mel_to_codes(self.local_modules['dvae'], mel)
        back_to_mel = self.local_modules['dvae'].decode(mel_codes)[0]
        orig_audio = audio
        real_resampled = torchaudio.functional.resample(audio, 22050, sample_rate).unsqueeze(0)

        output_size = real_resampled.shape[-1]
        aligned_mel_compression_factor = output_size // back_to_mel.shape[-1]
        padded_size = ceil_multiple(output_size, 2048)
        padding_added = padded_size - output_size
        padding_needed_for_codes = padding_added // aligned_mel_compression_factor
        if padding_needed_for_codes > 0:
            back_to_mel = F.pad(back_to_mel, (0, padding_needed_for_codes))
        output_shape = (1, 1, padded_size)
        gen = self.diffuser.p_sample_loop(self.model, output_shape,
                                    model_kwargs={'spectrogram': back_to_mel,
                                                  'conditioning_input': orig_audio.unsqueeze(0)})

        # Pop it back down to 5.5kHz for an accurate comparison with the other diffusers.
        real_resampled = torchaudio.functional.resample(real_resampled.squeeze(0), sample_rate, 5500).unsqueeze(0)
        gen = torchaudio.functional.resample(gen.squeeze(0), sample_rate, 5500).unsqueeze(0)
        return gen, real_resampled, 5500


    def perform_diffusion_vocoder(self, audio, codes, text, sample_rate=5500):
        mel = wav_to_mel(audio)
        mel_codes = convert_mel_to_codes(self.local_modules['dvae'], mel)
        text_codes = text_to_sequence(text)
        real_resampled = torchaudio.functional.resample(audio, 22050, sample_rate).unsqueeze(0)

        output_size = real_resampled.shape[-1]
        aligned_codes_compression_factor = output_size // mel_codes.shape[-1]
        padded_size = ceil_multiple(output_size, 2048)
        padding_added = padded_size - output_size
        padding_needed_for_codes = padding_added // aligned_codes_compression_factor
        if padding_needed_for_codes > 0:
            mel_codes = F.pad(mel_codes, (0, padding_needed_for_codes))
        output_shape = (1, 1, padded_size)
        gen = self.diffuser.p_sample_loop(self.model, output_shape,
                                    model_kwargs={'tokens': mel_codes,
                                                  'conditioning_input': audio.unsqueeze(0),
                                                  'unaligned_input': torch.tensor(text_codes, device=audio.device).unsqueeze(0)})
        return gen, real_resampled, sample_rate


    def perform_diffusion_tts9_mel_from_codes(self, audio, codes, text):
        SAMPLE_RATE = 24000
        mel = wav_to_mel(audio)
        mel_codes = convert_mel_to_codes(self.local_modules['dvae'], mel)
        real_resampled = torchaudio.functional.resample(audio, 22050, SAMPLE_RATE).unsqueeze(0)
        univnet_mel = wav_to_univnet_mel(real_resampled, do_normalization=False)  # to be used for a conditioning input, but also guides output shape.

        output_size = univnet_mel.shape[-1]
        aligned_codes_compression_factor = output_size // mel_codes.shape[-1]
        if hasattr(self.model, 'alignment_size'):
            padded_size = ceil_multiple(output_size, self.model.alignment_size)
            padding_added = padded_size - output_size
            padding_needed_for_codes = padding_added // aligned_codes_compression_factor
            if padding_needed_for_codes > 0:
                mel_codes = F.pad(mel_codes, (0, padding_needed_for_codes))
            output_shape = (1, 100, padded_size)
        else:
            output_shape = univnet_mel.shape
        gen_mel = self.diffuser.p_sample_loop(self.model, output_shape,
                                    model_kwargs={'aligned_conditioning': mel_codes,
                                                  'conditioning_input': univnet_mel})
        # denormalize mel
        gen_mel = denormalize_tacotron_mel(gen_mel)

        gen_wav = self.local_modules['vocoder'].inference(gen_mel)
        real_dec = self.local_modules['vocoder'].inference(univnet_mel)
        return gen_wav.float(), real_dec, SAMPLE_RATE

    def load_projector(self):
        """
        Builds the CLIP model used to project speech into a latent. This model has fixed parameters and a fixed loading
        path for the time being.
        """
        model = MelTextCLIP(dim_text=512, dim_latent=512, dim_speech=512, num_text_tokens=148, text_enc_depth=8,
                            text_seq_len=400, text_heads=8, speech_enc_depth=10, speech_heads=8, speech_seq_len=1000,
                            text_mask_percentage=.15, voice_mask_percentage=.15)
        weights = torch.load('../experiments/clip_text_to_voice_for_speech_fid.pth')
        model.load_state_dict(weights)
        return model

    def project(self, projector, sample, sample_rate):
        sample = torchaudio.functional.resample(sample, sample_rate, 22050)
        mel = wav_to_mel(sample)
        return projector.get_speech_projection(mel).squeeze(0)  # Getting rid of the batch dimension means it's just [hidden_dim]

    def load_w2v(self):
        return Wav2Vec2ForCTC.from_pretrained("jbetker/wav2vec2-large-robust-ft-libritts-voxpopuli")

    def intelligibility_loss(self, w2v, sample, real_sample, sample_rate, real_text):
        """
        Measures the differences between CTC losses using wav2vec2 against the real sample and the generated sample.
        """
        text_codes = torch.tensor(text_to_sequence(real_text), device=sample.device)
        results = []
        for s in [sample, real_sample]:
            s = torchaudio.functional.resample(s, sample_rate, 16000)
            norm_s = (s - s.mean()) / torch.sqrt(s.var() + 1e-7)
            norm_s = norm_s.squeeze(1)
            loss = w2v(input_values=norm_s, labels=text_codes).loss
            results.append(loss)
        gen_loss, real_loss = results
        return gen_loss - real_loss


    def compute_frechet_distance(self, proj1, proj2):
        # I really REALLY FUCKING HATE that this is going to numpy. Why does "pytorch_fid" operate in numpy land. WHY?
        proj1 = proj1.cpu().numpy()
        proj2 = proj2.cpu().numpy()
        mu1 = np.mean(proj1, axis=0)
        mu2 = np.mean(proj2, axis=0)
        sigma1 = np.cov(proj1, rowvar=False)
        sigma2 = np.cov(proj2, rowvar=False)
        return torch.tensor(calculate_frechet_distance(mu1, sigma1, mu2, sigma2))

    def perform_eval(self):
        save_path = osp.join(self.env['base_path'], "../", "audio_eval", str(self.env["step"]))
        os.makedirs(save_path, exist_ok=True)

        projector = self.load_projector().to(self.env['device'])
        projector.eval()

        w2v = self.load_w2v().to(self.env['device'])
        w2v.eval()
        for k, mod in self.local_modules.items():
            self.local_modules[k] = mod.to(self.env['device'])

        # Attempt to fix the random state as much as possible. RNG state will be restored before returning.
        rng_state = torch.get_rng_state()
        torch.manual_seed(5)
        self.model.eval()

        with torch.no_grad():
            gen_projections = []
            real_projections = []
            intelligibility_losses = []
            for i in tqdm(list(range(0, len(self.data), self.skip))):
                path, text, codes = self.data[i + self.env['rank']]
                audio = load_audio(path, 22050).to(self.dev)
                codes = codes.to(self.dev)
                sample, ref, sample_rate = self.diffusion_fn(audio, codes, text)

                gen_projections.append(self.project(projector, sample, sample_rate).cpu())  # Store on CPU to avoid wasting GPU memory.
                real_projections.append(self.project(projector, ref, sample_rate).cpu())
                intelligibility_losses.append(self.intelligibility_loss(w2v, sample, ref, sample_rate, text))

                torchaudio.save(os.path.join(save_path, f"{self.env['rank']}_{i}_gen.wav"), sample.squeeze(0).cpu(), sample_rate)
                torchaudio.save(os.path.join(save_path, f"{self.env['rank']}_{i}_real.wav"), ref.squeeze(0).cpu(), sample_rate)
            gen_projections = torch.stack(gen_projections, dim=0)
            real_projections = torch.stack(real_projections, dim=0)
            intelligibility_loss = torch.stack(intelligibility_losses, dim=0).mean()
            frechet_distance = torch.tensor(self.compute_frechet_distance(gen_projections, real_projections), device=self.env['device'])

            if distributed.is_initialized() and distributed.get_world_size() > 1:
                distributed.all_reduce(frechet_distance)
                frechet_distance = frechet_distance / distributed.get_world_size()
                distributed.all_reduce(intelligibility_loss)
                intelligibility_loss = intelligibility_loss / distributed.get_world_size()

        self.model.train()
        torch.set_rng_state(rng_state)

        # Put modules used for evaluation back into CPU memory.
        for k, mod in self.local_modules.items():
            self.local_modules[k] = mod.cpu()

        return {"frechet_distance": frechet_distance, "intelligibility_loss": intelligibility_loss}

"""
if __name__ == '__main__':
    from utils.util import load_model_from_config

    diffusion = load_model_from_config('X:\\dlas\\experiments\\train_diffusion_tts7_dvae_thin_with_text.yml', 'generator',
                                       also_load_savepoint=False, load_path='X:\\dlas\\experiments\\train_diffusion_tts7_dvae_thin_with_text\\models\\56500_generator_ema.pth').cuda()
    opt_eval = {'eval_tsv': 'Y:\\libritts\\test-clean\\transcribed-brief-w2v.tsv', 'diffusion_steps': 100,
                'conditioning_free': False, 'conditioning_free_k': 1,
                'diffusion_schedule': 'linear', 'diffusion_type': 'vocoder'}
    env = {'rank': 0, 'base_path': 'D:\\tmp\\test_eval', 'step': 2, 'device': 'cuda', 'opt': {}}
    eval = AudioDiffusionFid(diffusion, opt_eval, env)
    print(eval.perform_eval())
"""


if __name__ == '__main__':
    from utils.util import load_model_from_config

    diffusion = load_model_from_config('X:\\dlas\\experiments\\train_diffusion_tts_mel_flat.yml', 'generator',
                                       also_load_savepoint=False,
                                       load_path='X:\\dlas\\experiments\\train_diffusion_tts_mel_flat\\models\\19500_generator_ema.pth').cuda()
    opt_eval = {'eval_tsv': 'Y:\\libritts\\test-clean\\transcribed-brief-w2v.tsv', 'diffusion_steps': 100,
                'conditioning_free': False, 'conditioning_free_k': 1,
                'diffusion_schedule': 'linear', 'diffusion_type': 'tts9_mel'}
    env = {'rank': 0, 'base_path': 'D:\\tmp\\test_eval', 'step': 558, 'device': 'cuda', 'opt': {}}
    eval = AudioDiffusionFid(diffusion, opt_eval, env)
    print(eval.perform_eval())
