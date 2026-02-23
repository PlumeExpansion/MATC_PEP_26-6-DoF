<script lang='ts'>
	import { Pane, Folder, Binding, Monitor, Button, Slider, TabGroup, TabPage, Color, Point,
		List, type ListOptions, type ListChangeEvent,
		ButtonGrid, type ButtonGridClickEvent } from 'svelte-tweakpane-ui'
	import { TelemetryManager } from './telem_manager.svelte.js';

	let { tm }: { tm: TelemetryManager } = $props();

	let isDisconnected = $derived(tm.socketParams.status == 'Disconnected');
	let isConnected = $derived(tm.socketParams.status == 'Connected');
	let connectBtnTitle = $derived(isConnected? 'Connected' : 'Connect');

	const telems = ['Build','Raw','Misc','Hull','Surfaced','Propulsor'];
	const wingTelems = ['Root','Main','Rear'];
	function getTelem(title: string) {
		switch (title) {
			case 'Build': return tm.telem.build;
			case 'Raw': return tm.telem.raw;
			case 'Misc': return tm.telem.misc;
			case 'Hull': return tm.telem.hull;
			case 'Surfaced': return tm.telem.surf;
			case 'Propulsor': return tm.telem.propulsor;
			case 'Root': return tm.telem.wings.root;
			case 'Main': return tm.telem.wings.main;
			case 'Rear': return tm.telem.wings.rear;
		}
	}
	function onTelemClick(event: ButtonGridClickEvent) {
		console.log(getTelem(event.detail.label))
	}
</script>

<Pane title='' x={0} y={0} width={256} localStoreId='leftPane'>
	<Folder title='Websocket'>
		<Binding bind:object={tm.socketParams} key='url' label='address' />
		<Monitor value={tm.socketParams.status} label='status' />
		<Button on:click={() => tm.callbacks.onConnect(tm.socketParams.url)} 
			title={connectBtnTitle}
			disabled={!isDisconnected} />
	</Folder>
	<Folder title='Telemetry' disabled={!isConnected}>
		<ButtonGrid on:click={onTelemClick} buttons={telems} />
		<Folder title='Wings'>
			<ButtonGrid on:click={onTelemClick} buttons={wingTelems} rows={1} />
		</Folder>
	</Folder>
	<Folder title='Simulation' disabled={!isConnected}>
		<Monitor value={tm.simStates.rate} label='rate' />
		<Slider bind:value={tm.controlStates.rate} 
			min={0} max={1} format={v => v.toFixed(1)} label='target'/>
		<List bind:value={tm.simStates.method} label='method' options={tm.methods} 
			on:change={ev => {
				if (ev.detail.value != tm.simStates.method)
					tm.callbacks.onStateChange('method', ev.detail.value)
			}}/>
		<Slider bind:value={tm.controlStates.dt} 
			min={0.001} max={0.1} format={v => v.toFixed(3)} label='Δt'/>
		<ButtonGrid on:click={ev => {
			switch (ev.detail.label) {
				case 'Resume':
				case 'Pause':
					tm.simStates.cmdQueued = true;
					tm.callbacks.onToggleRun();
					break;
				case 'Step':
					tm.callbacks.onStep();
					break;
			}
		}} buttons={[tm.simStates.running? 'Pause' : 'Resume', 'Step']} rows={1} disabled={tm.simStates.cmdQueued}/>
		<ButtonGrid on:click={ev => {
			switch (ev.detail.label) {
				case 'Reset':
					tm.callbacks.onReset();
					break;
				case 'Re-initialize':
					tm.callbacks.onReinit();
					break;
			}
		}} buttons={['Reset','Re-initialize']}  rows={1} />
	</Folder>
	<Folder title='Camera'>
		<Button on:click={() => tm.callbacks.onRefocusCamera()}  title='Refocus Camera' />
		<ButtonGrid on:click={ev => {
			switch (ev.detail.label) {
				case 'Free':
					tm.sceneConfig.cameraFollow = false;
					break;
				case 'Follow':
					tm.sceneConfig.cameraFollow = true;
					break;
			}
		}} buttons={['Free','Follow']}  rows={1} />
		<Folder title='Track'>
			<ButtonGrid on:click={ev => tm.sceneConfig.cameraTrack = ev.detail.label} buttons={['None','Body','Buoy']} rows={1} />
		</Folder>
	</Folder>
	<Folder title='Scene'>
		<ButtonGrid on:click={ev => {
			switch (ev.detail.label) {
				case 'Lighting':
					tm.callbacks.onToggleLightHelpers();
					break;
				case 'Buoys':
					tm.callbacks.onToggleBuoys();
					break;
			}
		}} buttons={['Lighting','Buoys']} rows={1} />
		<Folder title='STL'>
			<Slider bind:value={tm.sceneConfig.stlOpacity} 
				min={0} max={1} format={v => v.toFixed(1)} label='opacity' on:change={() => tm.callbacks.onStlOpacity()}/>
			<ButtonGrid on:click={ev => {
				switch (ev.detail.label) {
					case 'Hull':
						tm.callbacks.onToggleHull();
						break;
					case 'Wings':
						tm.callbacks.onToggleWings();
						break;
					case 'Rear Wings':
						tm.callbacks.onToggleRearWings();
						break;
				}
			}} buttons={['Hull','Wings','Rear Wings']} rows={1} />
		</Folder>
		<Folder title='Waterplane'>
			<Slider bind:value={tm.sceneConfig.waterplaneOpacity} 
				min={0} max={1} format={v => v.toFixed(1)} label='opacity' on:change={() => tm.callbacks.onVisuals()}/>
			<Color bind:value={tm.sceneConfig.waterplaneColor} label='color' on:change={() => tm.callbacks.onVisuals()} />
			<ButtonGrid on:click={ev => {
				switch (ev.detail.label) {
					case 'Waterplane':
						tm.callbacks.onToggleWaterplane();
						break;
					case 'Grid':
						tm.callbacks.onToggleGrid();
						break;
				}
			}} buttons={['Waterplane','Grid']} rows={1} />
		</Folder>
	</Folder>
</Pane>

<Pane title='' x={window.innerWidth} y={0} width={270} localStoreId='rightPane'>
	<TabGroup>
		<TabPage title='Visuals' disabled={!isConnected}>
			<Folder title='Panels'>
				<Color bind:value={tm.sceneConfig.surfColor} label='surfaced' on:change={() => tm.callbacks.onVisuals()} />
				<Color bind:value={tm.sceneConfig.subColor} label='submerged' on:change={() => tm.callbacks.onVisuals()} />
				<Slider bind:value={tm.sceneConfig.submergenceScale} 
					min={0} max={0.5} format={v => v.toFixed(1)} label='submergence' on:change={() => tm.callbacks.onVisuals()}/>
				<ButtonGrid on:click={ev => {
					switch (ev.detail.label) {
						case 'Surfaced':
							tm.callbacks.onToggleSurfaced();
							break;
						case 'Submerged':
							tm.callbacks.onToggleSubmerged();
							break;
						case 'Submergence':
							tm.callbacks.onToggleSubmergence();
							break;
					}
				}} buttons={['Surfaced','Submerged','Submergence']} rows={1} />
			</Folder>
			<Folder title='Vectors'>
				<Color bind:value={tm.sceneConfig.forceColor} label='force' on:change={() => tm.callbacks.onVisuals()} />
				<Color bind:value={tm.sceneConfig.momentColor} label='moment' on:change={() => tm.callbacks.onVisuals()} />
				<Slider bind:value={tm.sceneConfig.forceScale} 
					min={0} max={0.002} format={v => v.toFixed(3)} label='force' on:change={() => tm.callbacks.onVisuals()}/>
				<Slider bind:value={tm.sceneConfig.momentScale} 
					min={0} max={0.02} format={v => v.toFixed(2)} label='moment' on:change={() => tm.callbacks.onVisuals()}/>
				<ButtonGrid on:click={ev => {
					switch (ev.detail.label) {
						case 'Forces':
							tm.callbacks.onToggleForces();
							break;
						case 'Moments':
							tm.callbacks.onToggleMoments();
							break;
					}
				}} buttons={['Forces','Moments']} rows={1} />
			</Folder>
			<Folder title='Axes'>
				<ButtonGrid on:click={ev => {
					switch (ev.detail.label) {
						case 'Hull':
							tm.callbacks.onToggleHullAxes();
							break;
						case 'Foil':
							tm.callbacks.onToggleFoilAxes();
							break;
						case 'Propulsor':
							tm.callbacks.onTogglePropulsorAxes();
							break;
					}
				}} buttons={['Hull','Foil','Propulsor']} rows={1} />
			</Folder>
			<Folder title='Frames'>
				<ButtonGrid on:click={ev => {
					switch (ev.detail.label) {
						case 'Fixed':
							tm.callbacks.onToggleFixedFrame();
							break;
						case 'Body':
							tm.callbacks.onToggleBodyFrame();
							break;
						case 'Rear Axle':
							tm.callbacks.onToggleRearAxleFrame();
							break;
					}
				}} buttons={['Fixed','Body','Rear Axle']} rows={1} />
			</Folder>
		</TabPage>
		<TabPage title='States' disabled={!isConnected}>
			<!-- <Button on:click={() => {
				ui.syncControlStates();
				ui.syncInputs();
			}}  title='Sync States' /> -->
			<Button on:click={() => tm.callbacks.onReset()}  title='Zero States' />
			<Folder title='Velocites'>
				<Monitor value={tm.simStates.U.u} label='u [m/s]' />
				<Monitor value={tm.simStates.U.v} label='v [m/s]' />
				<Monitor value={tm.simStates.U.w} label='w [m/s]' />
				<Point bind:value={tm.controlStates.U} label='<u,v,w>' 
					optionsX={{min: -5, max: 20}}
					optionsY={{min: -2, max: 2}}
					optionsZ={{min: -2, max: 2}} 
					on:change={ev => tm.callbacks.onStateChange('U', ev.detail)}
					disabled={tm.simStates.running}
					format={v => v.toFixed(2)}/>
			</Folder>
			<Folder title='Angular Rates'>
				<Monitor value={tm.simStates.omega.p} label='p [°/s]' />
				<Monitor value={tm.simStates.omega.q} label='q [°/s]' />
				<Monitor value={tm.simStates.omega.r} label='r [°/s]' />
				<Point bind:value={tm.controlStates.omega} label='<p,q,r>' 
					optionsX={{min: -60, max: 60}}
					optionsY={{min: -60, max: 60}}
					optionsZ={{min: -60, max: 60}} 
					on:change={ev => tm.callbacks.onStateChange('omega', ev.detail)}
					disabled={tm.simStates.running}
					format={v => v.toFixed(2)}/>
			</Folder>
			<Folder title='Euler Angles'>
				<Monitor value={tm.simStates.Phi.phi} label='ϕ [°]' />
				<Monitor value={tm.simStates.Phi.theta} label='θ [°]' />
				<Monitor value={tm.simStates.Phi.psi} label='ψ [°]' />
				<Point bind:value={tm.controlStates.Phi} label='<ϕ,θ,ψ>' 
					optionsX={{min: -60, max: 60}}
					optionsY={{min: -45, max: 45}}
					optionsZ={{min: -180, max: 180}}
					on:change={ev => tm.callbacks.onStateChange('Phi', ev.detail)}
					disabled={tm.simStates.running}
					format={v => v.toFixed(2)}/>
			</Folder>
			<Folder title='Position'>
				<Monitor value={tm.simStates.r.x} label='x [m]' />
				<Monitor value={tm.simStates.r.y} label='y [m]' />
				<Monitor value={tm.simStates.r.z} label='z [cm]' />
				<Point bind:value={tm.controlStates.r} label='<x,y,z>' 
					optionsZ={{min: -50, max: 50}} 
					on:change={ev => tm.callbacks.onStateChange('r', ev.detail)}
					disabled={tm.simStates.running}
					format={v => v.toFixed(1)}/>
			</Folder>
			<Folder title='Propulsor States'>
				<Button on:click={() => {
					tm.controlStates.input.x = 0;
					tm.controlStates.input.y = 0;
					tm.callbacks.onStateChange('input', { origin: 'internal', value: tm.controlStates.input });
				}}  title='Zero Inputs' />
				<Monitor value={tm.simStates.RPM} label='RPM' />
				<Monitor value={tm.simStates.I} label='I [A]' />
				<Monitor value={tm.simStates.psi_ra} label='ψ-ra [°]' />
				<Monitor value={tm.simStates.V} label='V [V]' />
				<Point bind:value={tm.controlStates.input} label='<%ψ,%V>' 
					optionsX={{min: -1, max: 1}}
					optionsY={{min: -1, max: 1, inverted: true}}
					picker='inline'
					expanded={true}
					on:change={ev => tm.callbacks.onStateChange('input', ev.detail)}
					format={v => v.toFixed(2)}/>
			</Folder>
		</TabPage>
	</TabGroup>
</Pane>